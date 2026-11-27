import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.photo import Photo


class Post(Base):
    """A blog post: a title, some text and an ordered set of photos."""

    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    slug: Mapped[str] = mapped_column(Text, unique=True)  # the URL name, e.g. seongsu-walk
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, server_default="")
    published: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    # Set the first time the post is published, and kept if it's unpublished and published again.
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    photos: Mapped[list["PostPhoto"]] = relationship(
        back_populates="post",
        order_by="PostPhoto.position",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PostPhoto(Base):
    """Which photos are in a post, in which order, with an optional caption.
    A separate table, so one photo can appear in several posts."""

    __tablename__ = "post_photos"

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    photo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    caption: Mapped[str | None] = mapped_column(Text)

    post: Mapped[Post] = relationship(back_populates="photos")
    photo: Mapped[Photo] = relationship(lazy="joined")
