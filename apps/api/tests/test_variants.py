import io

from PIL import Image

from app.services.variants import make_variant
from tests.images import T, make_image, sample_exif


def _open(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    img.load()
    return img


def test_thumb_fits_in_640_and_keeps_ratio():
    img = _open(make_variant(make_image(size=(4000, 3000)), "thumb"))
    assert img.format == "JPEG"
    assert img.size == (640, 480)


def test_display_never_upscales_small_photos():
    img = _open(make_variant(make_image(size=(800, 600)), "display"))
    assert img.size == (800, 600)


def test_rotation_is_applied_to_the_pixels():
    # Stored 4000x3000 but marked "rotate 90", so it's really a portrait photo.
    original = make_image(size=(4000, 3000), exif={**sample_exif(), T.Orientation: 6})
    img = _open(make_variant(original, "thumb"))
    assert img.size == (480, 640)


def test_exif_is_removed():
    img = _open(make_variant(make_image(size=(1000, 800), exif=sample_exif()), "thumb"))
    assert dict(img.getexif()) == {}


def test_png_with_transparency_becomes_jpeg():
    buf = io.BytesIO()
    Image.new("RGBA", (100, 100), (0, 0, 0, 0)).save(buf, "PNG")
    img = _open(make_variant(buf.getvalue(), "thumb"))
    assert img.format == "JPEG" and img.mode == "RGB"
