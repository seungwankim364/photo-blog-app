import re

from app.services.slug import MAX_LENGTH, SLUG_PATTERN, slugify, with_suffix


def test_title_to_slug():
    assert slugify("Seongsu Architecture Walk") == "seongsu-architecture-walk"
    assert slugify("  Café & Concrete: 2026!  ") == "cafe-concrete-2026"


def test_korean_only_title_gets_random_slug():
    slug = slugify("성수동 산책")
    assert re.fullmatch(r"post-[0-9a-f]{6}", slug)


def test_mixed_title_keeps_latin_part():
    assert slugify("성수동 Walk 2") == "walk-2"


def test_long_titles_are_cut():
    slug = slugify("word " * 50)
    assert len(slug) <= MAX_LENGTH and re.fullmatch(SLUG_PATTERN, slug)


def test_suffix():
    assert with_suffix("seongsu-walk", 2) == "seongsu-walk-2"
    assert len(with_suffix("a" * MAX_LENGTH, 12)) == MAX_LENGTH
