"""Endpoint tests. They use the local Postgres (after alembic upgrade head) and
skip when it isn't running. Files go to a temporary folder, and every photo a
test creates is deleted again."""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.main import app
from app.services.storage import LocalStorage, get_storage
from tests.images import make_image, sample_exif


def _database_ready() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM photos LIMIT 1"))
        return True
    except SQLAlchemyError:
        return False


pytestmark = pytest.mark.skipif(
    not _database_ready(), reason="needs Postgres with migrations applied"
)


@pytest.fixture
def storage(tmp_path):
    local = LocalStorage(tmp_path)
    app.dependency_overrides[get_storage] = lambda: local
    yield local
    app.dependency_overrides.clear()


@pytest.fixture
def client(storage):
    created = []
    with TestClient(app) as c:
        c.created = created
        yield c
        for photo_id in created:
            c.delete(f"/photos/{photo_id}")


def upload(client, data: bytes, name: str = "DSCF0001.JPG"):
    res = client.post("/photos", files={"file": (name, data, "image/jpeg")})
    if res.status_code == 201:
        client.created.append(res.json()["id"])
    return res


def test_upload_saves_file_and_exif(client, storage):
    data = make_image(exif=sample_exif())
    res = upload(client, data)

    assert res.status_code == 201
    body = res.json()
    assert body["original_filename"] == "DSCF0001.JPG"
    assert body["camera_model"] == "X-T5"
    assert body["shutter"] == "1/125"
    assert body["aperture"] == 2.8
    assert body["iso"] == 400
    assert body["taken_at"].startswith("2026-11-01T05:30:00")  # 14:30 +09:00 in UTC
    assert body["exif_raw"]["Make"] == "FUJIFILM"
    assert "storage_key" not in body

    files = list(storage.root.rglob("*.jpg"))
    assert len(files) == 1 and files[0].read_bytes() == data


def test_get_one_and_file(client):
    data = make_image(exif=sample_exif())
    photo_id = upload(client, data).json()["id"]

    res = client.get(f"/photos/{photo_id}")
    assert res.status_code == 200 and res.json()["id"] == photo_id

    res = client.get(f"/photos/{photo_id}/file")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"
    assert res.content == data


def test_resized_copies(client, storage):
    photo_id = upload(client, make_image(size=(3000, 2000), exif=sample_exif())).json()["id"]

    for size, expected in (("thumb", (640, 427)), ("display", (2048, 1365))):
        res = client.get(f"/photos/{photo_id}/file", params={"size": size})
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/jpeg"
        assert "immutable" in res.headers["cache-control"]
        assert Image.open(io.BytesIO(res.content)).size == expected

    # Made once, then served from storage.
    assert len(list(storage.root.rglob("variants/*/*.jpg"))) == 2


def test_unknown_size_is_rejected(client):
    photo_id = upload(client, make_image()).json()["id"]
    assert client.get(f"/photos/{photo_id}/file", params={"size": "huge"}).status_code == 422


def test_list_includes_upload(client):
    photo_id = upload(client, make_image(exif=sample_exif())).json()["id"]

    res = client.get("/photos", params={"limit": 200})
    assert res.status_code == 200
    assert photo_id in [p["id"] for p in res.json()]


def test_delete_removes_row_and_files(client, storage):
    photo_id = upload(client, make_image()).json()["id"]
    client.created.remove(photo_id)
    client.get(f"/photos/{photo_id}/file", params={"size": "thumb"})

    assert client.delete(f"/photos/{photo_id}").status_code == 204
    assert client.get(f"/photos/{photo_id}").status_code == 404
    assert list(storage.root.rglob("*.jpg")) == []


def test_rejects_non_images(client, storage):
    res = upload(client, b"not a photo", name="notes.txt")
    assert res.status_code == 415
    assert list(storage.root.rglob("*")) == []


def test_rejects_too_large(client, monkeypatch):
    monkeypatch.setattr("app.routers.photos.settings.max_upload_mb", 0)
    assert upload(client, make_image()).status_code == 413


def test_unknown_photo_is_404(client):
    assert client.get("/photos/00000000-0000-0000-0000-000000000000").status_code == 404
