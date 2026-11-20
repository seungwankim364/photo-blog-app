import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PhotoOut(BaseModel):
    """What the API returns for a photo. Leaves out storage details and the embedding."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    content_type: str
    size_bytes: int
    width: int | None
    height: int | None
    taken_at: datetime | None
    camera_make: str | None
    camera_model: str | None
    lens_model: str | None
    focal_length_mm: float | None
    focal_35mm: int | None
    aperture: float | None
    shutter: str | None
    iso: int | None
    created_at: datetime


class PhotoDetail(PhotoOut):
    """Single photo view, with every EXIF tag."""

    exif_raw: dict
