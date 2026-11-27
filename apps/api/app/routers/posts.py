import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Photo, Post, PostPhoto
from app.schemas.photo import PhotoOut
from app.schemas.post import (
    PostCreate,
    PostDetail,
    PostPhotoIn,
    PostPhotoOut,
    PostSummary,
    PostUpdate,
)
from app.services.slug import slugify, with_suffix

router = APIRouter(prefix="/posts", tags=["posts"])

# Until login (Cognito) exists, drafts are hidden unless asked for with
# include_drafts=true. The write endpoints are open too. Both get locked down
# when authentication is added.


@router.post("", response_model=PostDetail, status_code=status.HTTP_201_CREATED)
def create_post(data: PostCreate, session: Session = Depends(get_session)) -> PostDetail:
    if data.slug and _slug_taken(session, data.slug):
        raise HTTPException(status.HTTP_409_CONFLICT, f"slug '{data.slug}' is already used")

    post = Post(
        slug=data.slug or _free_slug(session, slugify(data.title)),
        title=data.title.strip(),
        body=data.body,
        published=data.published,
        published_at=datetime.now(UTC) if data.published else None,
    )
    post.photos = _photo_links(session, data.photos)
    session.add(post)
    _commit(session)
    return _detail(session, post)


@router.get("", response_model=list[PostSummary])
def list_posts(
    include_drafts: bool = False, session: Session = Depends(get_session)
) -> list[PostSummary]:
    """Newest first by publish date. Drafts (never published) come first when included."""
    stmt = select(Post).order_by(Post.published_at.desc().nulls_first(), Post.created_at.desc())
    if not include_drafts:
        stmt = stmt.where(Post.published.is_(True))
    return [_summary(post) for post in session.scalars(stmt)]


@router.get("/{slug}", response_model=PostDetail)
def get_post(
    slug: str, include_drafts: bool = False, session: Session = Depends(get_session)
) -> PostDetail:
    post = session.scalar(select(Post).where(Post.slug == slug))
    if post is None or (not post.published and not include_drafts):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "post not found")
    return _detail(session, post)


@router.patch("/{post_id}", response_model=PostDetail)
def update_post(
    post_id: uuid.UUID, data: PostUpdate, session: Session = Depends(get_session)
) -> PostDetail:
    post = _get_or_404(session, post_id)
    fields = data.model_fields_set

    if "slug" in fields and data.slug and data.slug != post.slug:
        if _slug_taken(session, data.slug):
            raise HTTPException(status.HTTP_409_CONFLICT, f"slug '{data.slug}' is already used")
        post.slug = data.slug
    if "title" in fields and data.title is not None:
        post.title = data.title.strip()
    if "body" in fields and data.body is not None:
        post.body = data.body
    if "published" in fields and data.published is not None:
        post.published = data.published
        if data.published and post.published_at is None:
            post.published_at = datetime.now(UTC)
    if "photos" in fields and data.photos is not None:
        links = _photo_links(session, data.photos)
        post.photos.clear()
        session.flush()  # removes the old rows before the new ones use the same keys
        post.photos.extend(links)

    post.updated_at = func.now()  # also when only the photos changed
    _commit(session)
    return _detail(session, post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: uuid.UUID, session: Session = Depends(get_session)) -> Response:
    """Deletes the post. Its photos stay, since they can be in other posts."""
    session.delete(_get_or_404(session, post_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _photo_links(session: Session, photos: list[PostPhotoIn]) -> list[PostPhoto]:
    ids = [p.photo_id for p in photos]
    found = set(session.scalars(select(Photo.id).where(Photo.id.in_(ids)))) if ids else set()
    missing = [str(i) for i in ids if i not in found]
    if missing:
        raise HTTPException(
            422, f"photos not found: {', '.join(missing)}"
        )
    return [
        PostPhoto(photo_id=p.photo_id, position=i, caption=(p.caption or "").strip() or None)
        for i, p in enumerate(photos)
    ]


def _slug_taken(session: Session, slug: str) -> bool:
    return session.scalar(select(Post.id).where(Post.slug == slug)) is not None


def _free_slug(session: Session, base: str) -> str:
    slug, n = base, 1
    while _slug_taken(session, slug):
        n += 1
        slug = with_suffix(base, n)
    return slug


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError:
        # Two requests took the same slug at the same moment. The unique index catches it.
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "slug is already used")


def _get_or_404(session: Session, post_id: uuid.UUID) -> Post:
    post = session.get(Post, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "post not found")
    return post


def _summary(post: Post) -> PostSummary:
    return PostSummary(
        id=post.id,
        slug=post.slug,
        title=post.title,
        published=post.published,
        published_at=post.published_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
        photo_count=len(post.photos),
        cover=PhotoOut.model_validate(post.photos[0].photo) if post.photos else None,
    )


def _detail(session: Session, post: Post) -> PostDetail:
    session.refresh(post)  # picks up server-set times and the saved photo order
    return PostDetail(
        **_summary(post).model_dump(),
        body=post.body,
        photos=[PostPhotoOut.model_validate(link) for link in post.photos],
    )
