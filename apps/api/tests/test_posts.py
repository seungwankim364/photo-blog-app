"""Post endpoint tests. Like test_photos.py, they use the local Postgres and
skip when it isn't running, and clean up everything they create."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.main import app
from app.services.storage import LocalStorage, get_storage
from tests.images import make_image, sample_exif


def _database_ready() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM posts LIMIT 1"))
        return True
    except SQLAlchemyError:
        return False


pytestmark = pytest.mark.skipif(
    not _database_ready(), reason="needs Postgres with migrations applied (0002)"
)


@pytest.fixture
def client(tmp_path):
    storage = LocalStorage(tmp_path)
    app.dependency_overrides[get_storage] = lambda: storage
    photos, posts = [], []
    with TestClient(app) as c:
        c.photos, c.posts = photos, posts
        yield c
        for post_id in posts:
            c.delete(f"/posts/{post_id}")
        for photo_id in photos:
            c.delete(f"/photos/{photo_id}")
    app.dependency_overrides.clear()


def new_photo(client) -> str:
    res = client.post("/photos", files={"file": ("p.jpg", make_image(exif=sample_exif()), "image/jpeg")})
    assert res.status_code == 201
    client.photos.append(res.json()["id"])
    return res.json()["id"]


def new_post(client, **fields):
    res = client.post("/posts", json={"title": "Seongsu Walk", **fields})
    if res.status_code == 201:
        client.posts.append(res.json()["id"])
    return res


def test_create_with_photos_in_order(client):
    a, b = new_photo(client), new_photo(client)
    res = new_post(
        client,
        body="First line\n\nSecond paragraph",
        published=True,
        photos=[{"photo_id": b, "caption": " Facade "}, {"photo_id": a}],
    )

    assert res.status_code == 201
    post = res.json()
    assert post["slug"].startswith("seongsu-walk")
    assert post["published"] is True and post["published_at"] is not None
    assert [p["photo"]["id"] for p in post["photos"]] == [b, a]
    assert post["photos"][0]["caption"] == "Facade"
    assert post["photos"][1]["caption"] is None
    assert post["photos"][0]["photo"]["camera_model"] == "X-T5"
    assert post["cover"]["id"] == b and post["photo_count"] == 2


def test_get_by_slug(client):
    slug = new_post(client, published=True).json()["slug"]
    res = client.get(f"/posts/{slug}")
    assert res.status_code == 200 and res.json()["title"] == "Seongsu Walk"


def test_drafts_are_hidden_unless_asked(client):
    draft = new_post(client).json()

    assert client.get(f"/posts/{draft['slug']}").status_code == 404
    assert draft["id"] not in [p["id"] for p in client.get("/posts").json()]

    assert client.get(f"/posts/{draft['slug']}", params={"include_drafts": True}).status_code == 200
    listed = client.get("/posts", params={"include_drafts": True}).json()
    assert draft["id"] in [p["id"] for p in listed]


def test_same_title_gets_next_slug(client):
    first = new_post(client, title="Concrete Stairs").json()["slug"]
    second = new_post(client, title="Concrete Stairs").json()["slug"]
    assert second == f"{first}-2"


def test_chosen_slug_that_is_taken_is_409(client):
    slug = new_post(client).json()["slug"]
    assert new_post(client, slug=slug).status_code == 409


def test_bad_slug_is_422(client):
    assert new_post(client, slug="Not A Slug!").status_code == 422


def test_unknown_or_repeated_photo_is_422(client):
    a = new_photo(client)
    assert new_post(client, photos=[{"photo_id": "00000000-0000-0000-0000-000000000000"}]).status_code == 422
    assert new_post(client, photos=[{"photo_id": a}, {"photo_id": a}]).status_code == 422


def test_update_fields_and_reorder_photos(client):
    a, b, c = new_photo(client), new_photo(client), new_photo(client)
    post = new_post(client, photos=[{"photo_id": a}, {"photo_id": b}]).json()

    res = client.patch(
        f"/posts/{post['id']}",
        json={"title": "Renamed", "photos": [{"photo_id": c}, {"photo_id": a, "caption": "kept"}]},
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["title"] == "Renamed"
    assert updated["slug"] == post["slug"]  # renaming doesn't move the URL
    assert updated["body"] == post["body"]  # fields not sent are unchanged
    assert [p["photo"]["id"] for p in updated["photos"]] == [c, a]
    assert updated["photos"][1]["caption"] == "kept"


def test_publish_sets_date_once(client):
    post = new_post(client).json()
    assert post["published_at"] is None

    first = client.patch(f"/posts/{post['id']}", json={"published": True}).json()["published_at"]
    client.patch(f"/posts/{post['id']}", json={"published": False})
    again = client.patch(f"/posts/{post['id']}", json={"published": True}).json()["published_at"]
    assert first is not None and again == first


def test_change_slug(client):
    post = new_post(client, published=True).json()
    res = client.patch(f"/posts/{post['id']}", json={"slug": "new-url"})
    assert res.status_code == 200 and res.json()["slug"] == "new-url"
    assert client.get("/posts/new-url").status_code == 200


def test_delete_post_keeps_photos(client):
    a = new_photo(client)
    post = new_post(client, photos=[{"photo_id": a}]).json()
    client.posts.remove(post["id"])

    assert client.delete(f"/posts/{post['id']}").status_code == 204
    assert client.get(f"/posts/{post['slug']}", params={"include_drafts": True}).status_code == 404
    assert client.get(f"/photos/{a}").status_code == 200


def test_deleting_a_photo_removes_it_from_posts(client):
    a, b = new_photo(client), new_photo(client)
    post = new_post(client, photos=[{"photo_id": a}, {"photo_id": b}]).json()
    client.photos.remove(a)

    assert client.delete(f"/photos/{a}").status_code == 204
    after = client.get(f"/posts/{post['slug']}", params={"include_drafts": True}).json()
    assert [p["photo"]["id"] for p in after["photos"]] == [b]


def test_unknown_post_is_404(client):
    missing = "00000000-0000-0000-0000-000000000000"
    assert client.get("/posts/no-such-post").status_code == 404
    assert client.patch(f"/posts/{missing}", json={"title": "x"}).status_code == 404
    assert client.delete(f"/posts/{missing}").status_code == 404
