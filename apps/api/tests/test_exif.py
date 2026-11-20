from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.services.exif import UnsupportedImage, format_shutter, read_image
from tests.images import T, make_image, sample_exif


def test_reads_blog_fields():
    info = read_image(make_image(exif=sample_exif()))

    assert info.content_type == "image/jpeg"
    assert info.extension == ".jpg"
    assert (info.width, info.height) == (40, 30)
    assert info.camera_make == "FUJIFILM"
    assert info.camera_model == "X-T5"
    assert info.lens_model == "XF23mmF1.4 R LM WR"
    assert info.aperture == Decimal("2.80")
    assert info.shutter == "1/125"
    assert info.iso == 400
    assert info.focal_length_mm == Decimal("23.00")
    assert info.focal_35mm == 35
    assert info.taken_at == datetime(2026, 11, 1, 14, 30, tzinfo=timezone(timedelta(hours=9)))
    assert info.exif_raw["Model"] == "X-T5"


def test_time_without_offset_uses_default_timezone():
    exif = sample_exif()
    del exif[T.OffsetTimeOriginal]
    info = read_image(make_image(exif=exif))

    assert info.taken_at.utcoffset() == timedelta(hours=9)  # EXIF_DEFAULT_TZ=Asia/Seoul


def test_rotated_photo_reports_displayed_size():
    info = read_image(make_image(size=(40, 30), exif={**sample_exif(), T.Orientation: 6}))
    assert (info.width, info.height) == (30, 40)


def test_photo_without_exif():
    info = read_image(make_image(fmt="PNG"))

    assert info.content_type == "image/png"
    assert info.taken_at is None
    assert info.camera_model is None
    assert info.exif_raw == {}


def test_mpo_is_treated_as_jpeg():
    info = read_image(make_image(fmt="MPO", exif=sample_exif()))

    assert info.format == "MPO"
    assert info.content_type == "image/jpeg"
    assert info.extension == ".jpg"
    assert info.camera_model == "X-T5"


def test_rejects_non_images():
    with pytest.raises(UnsupportedImage):
        read_image(b"definitely not a photo")


def test_rejects_unsupported_formats():
    with pytest.raises(UnsupportedImage):
        read_image(make_image(fmt="GIF"))


@pytest.mark.parametrize(
    ("seconds", "shown"),
    [(1 / 125, "1/125"), (1 / 4000, "1/4000"), (0.5, "1/2"), (1, "1s"), (2, "2s"), (1.3, "1.3s"), (0, None), (None, None)],
)
def test_format_shutter(seconds, shown):
    assert format_shutter(seconds) == shown
