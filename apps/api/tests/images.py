"""Builds small test images in memory, with whatever EXIF a test needs."""

import io

from PIL import ExifTags, Image
from PIL.TiffImagePlugin import IFDRational

T = ExifTags.Base


def make_image(fmt: str = "JPEG", size=(40, 30), exif: dict | None = None) -> bytes:
    img = Image.new("RGB", size, (120, 140, 160))
    buf = io.BytesIO()
    if exif is None:
        img.save(buf, fmt)
        return buf.getvalue()

    data = Image.Exif()
    sub = data.get_ifd(ExifTags.IFD.Exif)
    for tag, value in exif.items():
        # Camera and orientation live in the main block, shooting settings in the Exif block.
        target = data if tag in (T.Make, T.Model, T.Orientation, T.DateTime) else sub
        target[tag] = value
    extra = {"save_all": True, "append_images": [img.copy()]} if fmt == "MPO" else {}
    img.save(buf, fmt, exif=data.tobytes(), **extra)
    return buf.getvalue()


def sample_exif() -> dict:
    return {
        T.Make: "FUJIFILM",
        T.Model: "X-T5",
        T.LensModel: "XF23mmF1.4 R LM WR",
        T.DateTimeOriginal: "2026:11:01 14:30:00",
        T.OffsetTimeOriginal: "+09:00",
        T.FNumber: IFDRational(28, 10),
        T.ExposureTime: IFDRational(1, 125),
        T.ISOSpeedRatings: 400,
        T.FocalLength: IFDRational(23, 1),
        T.FocalLengthIn35mmFilm: 35,
    }
