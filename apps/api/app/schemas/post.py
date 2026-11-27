import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.photo import PhotoOut
from app.services.slug import MAX_LENGTH, SLUG_PATTERN


class PostPhotoIn(BaseModel):
    photo_id: uuid.UUID
    caption: str | None = Field(default=None, max_length=500)


def _unique_photos(photos: list[PostPhotoIn] | None) -> list[PostPhotoIn] | None:
    if photos is not None:
        ids = [p.photo_id for p in photos]
        if len(ids) != len(set(ids)):
            raise ValueError("a photo can only appear once in a post")
    return photos


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    # Left out, it's made from the title.
    slug: str | None = Field(default=None, max_length=MAX_LENGTH, pattern=SLUG_PATTERN)
    body: str = Field(default="", max_length=50_000)
    published: bool = False
    # In display order.
    photos: list[PostPhotoIn] = Field(default_factory=list, max_length=100)

    _check_photos = field_validator("photos")(_unique_photos)


class PostUpdate(BaseModel):
    """Only the fields sent are changed. `photos`, when sent, replaces the whole list."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=MAX_LENGTH, pattern=SLUG_PATTERN)
    body: str | None = Field(default=None, max_length=50_000)
    published: bool | None = None
    photos: list[PostPhotoIn] | None = Field(default=None, max_length=100)

    _check_photos = field_validator("photos")(_unique_photos)


class PostPhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position: int
    caption: str | None
    photo: PhotoOut


class PostSummary(BaseModel):
    """A post in a list: no body, the first photo as the cover."""

    id: uuid.UUID
    slug: str
    title: str
    published: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    photo_count: int
    cover: PhotoOut | None


class PostDetail(PostSummary):
    body: str
    photos: list[PostPhotoOut]
