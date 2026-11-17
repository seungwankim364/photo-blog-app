import uuid
from datetime import datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, Integer, Numeric, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# CLIP ViT-B/32 produces 512-dimensional embeddings.
# Changing the model later means a migration that changes this size.
EMBEDDING_DIM = 512


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Where the original file lives: a local path now, an S3 key later.
    storage_key: Mapped[str] = mapped_column(Text, unique=True)
    original_filename: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(Text)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)

    # EXIF fields shown on the blog. Read once from the original at upload.
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    camera_make: Mapped[str | None] = mapped_column(Text)
    camera_model: Mapped[str | None] = mapped_column(Text)
    lens_model: Mapped[str | None] = mapped_column(Text)
    focal_length_mm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    focal_35mm: Mapped[int | None] = mapped_column(Integer)
    aperture: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    shutter: Mapped[str | None] = mapped_column(Text)  # stored as shown, e.g. "1/125"
    iso: Mapped[int | None] = mapped_column(Integer)

    # Every EXIF tag, so new fields can be shown later without re-reading files.
    exif_raw: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    # Filled in by the classify worker in a later phase.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
