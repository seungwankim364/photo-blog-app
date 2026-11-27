"""URL names for posts: "Seongsu Architecture Walk" -> "seongsu-architecture-walk"."""

import re
import secrets
import unicodedata

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
MAX_LENGTH = 80


def slugify(title: str) -> str:
    """Lowercase ASCII words joined by dashes. A title with no Latin letters or
    digits (e.g. Korean only) gets a short random slug, which can be edited later."""
    ascii_text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    slug = slug[:MAX_LENGTH].rstrip("-")
    return slug or f"post-{secrets.token_hex(3)}"


def with_suffix(slug: str, n: int) -> str:
    """seongsu-walk, seongsu-walk-2, seongsu-walk-3 ..."""
    suffix = f"-{n}"
    return slug[: MAX_LENGTH - len(suffix)].rstrip("-") + suffix
