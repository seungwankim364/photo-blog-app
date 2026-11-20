"""Resized JPEG copies of an original, for the gallery and the photo page.

Originals can be 6 MB HEICs that most browsers can't show. These copies are
small, rotated the right way up, always JPEG, and carry no EXIF (so no GPS).
They are made the first time they are asked for and saved after that. Later
a worker makes them right after upload and they live in S3.
"""

import io
import uuid
from typing import Literal

from PIL import Image, ImageOps

from app.services import exif  # noqa: F401  registers the HEIC opener

Size = Literal["thumb", "display"]

MAX_EDGE: dict[str, int] = {"thumb": 640, "display": 2048}
QUALITY: dict[str, int] = {"thumb": 80, "display": 88}


def variant_key(photo_id: uuid.UUID, size: str) -> str:
    return f"variants/{photo_id}/{size}.jpg"


def all_variant_keys(photo_id: uuid.UUID) -> list[str]:
    return [variant_key(photo_id, size) for size in MAX_EDGE]


def make_variant(original: bytes, size: str) -> bytes:
    edge = MAX_EDGE[size]
    with Image.open(io.BytesIO(original)) as img:
        img = ImageOps.exif_transpose(img)  # apply the camera's rotation to the pixels
        img = img.convert("RGB")
        img.thumbnail((edge, edge), Image.Resampling.LANCZOS)  # keeps the aspect ratio, never upscales
        out = io.BytesIO()
        img.save(out, "JPEG", quality=QUALITY[size], optimize=True, progressive=True)
    return out.getvalue()
