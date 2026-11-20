"""Reads the image type, size and EXIF fields shown on the blog."""

import io
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from zoneinfo import ZoneInfo

import pillow_heif
from PIL import ExifTags, Image, UnidentifiedImageError

from app.config import settings

pillow_heif.register_heif_opener()  # lets Pillow open iPhone HEIC files

# Pillow's format name -> (content type, file extension)
SUPPORTED_FORMATS = {
    "JPEG": ("image/jpeg", ".jpg"),
    # MPO is a JPEG with extra small images inside (phones and some cameras write it).
    # Browsers show it as a normal JPEG, so it is stored as one.
    "MPO": ("image/jpeg", ".jpg"),
    "HEIF": ("image/heic", ".heic"),
    "PNG": ("image/png", ".png"),
}

T = ExifTags.Base
ORIENTATION_ROTATED = {5, 6, 7, 8}  # stored sideways, shown rotated 90 degrees
SKIP_IN_RAW = {T.MakerNote, T.UserComment, T.PrintImageMatching}


class UnsupportedImage(Exception):
    pass


@dataclass
class ImageInfo:
    format: str
    content_type: str
    extension: str
    width: int
    height: int
    taken_at: datetime | None = None
    camera_make: str | None = None
    camera_model: str | None = None
    lens_model: str | None = None
    focal_length_mm: Decimal | None = None
    focal_35mm: int | None = None
    aperture: Decimal | None = None
    shutter: str | None = None
    iso: int | None = None
    exif_raw: dict = field(default_factory=dict)


def read_image(data: bytes) -> ImageInfo:
    """Identifies the file by its content (not its name) and reads its EXIF."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            fmt = img.format
            width, height = img.size
            exif = img.getexif()
    except (UnidentifiedImageError, OSError) as e:
        raise UnsupportedImage("not a readable image") from e

    if fmt not in SUPPORTED_FORMATS:
        raise UnsupportedImage(f"unsupported format: {fmt}")
    content_type, extension = SUPPORTED_FORMATS[fmt]

    tags = {**dict(exif), **dict(exif.get_ifd(ExifTags.IFD.Exif))}

    # Width and height as the photo is displayed, not as stored.
    if tags.get(T.Orientation) in ORIENTATION_ROTATED:
        width, height = height, width

    return ImageInfo(
        format=fmt,
        content_type=content_type,
        extension=extension,
        width=width,
        height=height,
        taken_at=_taken_at(tags),
        camera_make=_text(tags.get(T.Make)),
        camera_model=_text(tags.get(T.Model)),
        lens_model=_text(tags.get(T.LensModel)),
        focal_length_mm=_decimal(tags.get(T.FocalLength), 2),
        focal_35mm=_int(tags.get(T.FocalLengthIn35mmFilm)),
        aperture=_decimal(tags.get(T.FNumber), 2),
        shutter=format_shutter(tags.get(T.ExposureTime)),
        iso=_int(tags.get(T.ISOSpeedRatings)),
        exif_raw=_raw(tags),
    )


def format_shutter(value) -> str | None:
    """0.008 -> "1/125", 0.5 -> "1/2", 2 -> "2s", 1.3 -> "1.3s"."""
    seconds = _float(value)
    if seconds is None or seconds <= 0:
        return None
    if seconds < 1:
        return f"1/{round(1 / seconds)}"
    return f"{seconds:g}s"


def _taken_at(tags: dict) -> datetime | None:
    raw = _text(tags.get(T.DateTimeOriginal) or tags.get(T.DateTime))
    if not raw:
        return None
    try:
        local = datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None

    offset = _text(tags.get(T.OffsetTimeOriginal) or tags.get(T.OffsetTime))
    tz = _parse_offset(offset) if offset else None
    return local.replace(tzinfo=tz or ZoneInfo(settings.exif_default_tz))


def _parse_offset(value: str) -> timezone | None:
    """"+09:00" -> UTC+9."""
    try:
        sign = -1 if value[0] == "-" else 1
        hours, minutes = value.lstrip("+-").split(":")
        return timezone(sign * timedelta(hours=int(hours), minutes=int(minutes)))
    except (ValueError, IndexError):
        return None


def _text(value) -> str | None:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if not isinstance(value, str):
        return None
    value = value.strip("\x00 ").strip()
    return value or None


def _float(value) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    return result if result == result else None  # drop NaN (0/0 rationals)


def _int(value) -> int | None:
    if isinstance(value, (tuple, list)):
        value = value[0] if value else None
    number = _float(value)
    return int(number) if number is not None else None


def _decimal(value, places: int) -> Decimal | None:
    number = _float(value)
    return round(Decimal(str(number)), places) if number is not None else None


def _raw(tags: dict) -> dict:
    """Every readable tag by name, as plain JSON values for the exif_raw column."""
    raw = {}
    for tag_id, value in tags.items():
        if tag_id in SKIP_IN_RAW or tag_id in (ExifTags.IFD.Exif, ExifTags.IFD.GPSInfo):
            continue
        name = ExifTags.TAGS.get(tag_id)
        json_value = _json_value(value)
        if name and json_value is not None:
            raw[name] = json_value
    return raw


def _json_value(value):
    if isinstance(value, (str, bytes)):
        return _text(value)
    if isinstance(value, bool) or isinstance(value, int):
        return value
    if isinstance(value, (float, Fraction)) or hasattr(value, "numerator"):
        return _float(value)
    if isinstance(value, (tuple, list)):
        items = [_json_value(v) for v in value]
        return items if all(i is not None for i in items) else None
    return None
