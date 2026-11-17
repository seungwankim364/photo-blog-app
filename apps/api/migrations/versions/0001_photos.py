"""Enable pgvector and create the photos table

Revision ID: 0001
Revises:
Create Date: 2026-11-17
"""
import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The app enables pgvector itself, so the same migration works on a local
    # container and on RDS. IF NOT EXISTS makes it safe if it was enabled by hand.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "photos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("storage_key", sa.Text(), nullable=False, unique=True),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("taken_at", sa.DateTime(timezone=True)),
        sa.Column("camera_make", sa.Text()),
        sa.Column("camera_model", sa.Text()),
        sa.Column("lens_model", sa.Text()),
        sa.Column("focal_length_mm", sa.Numeric(6, 2)),
        sa.Column("focal_35mm", sa.Integer()),
        sa.Column("aperture", sa.Numeric(4, 2)),
        sa.Column("shutter", sa.Text()),
        sa.Column("iso", sa.Integer()),
        sa.Column(
            "exif_raw",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("embedding", Vector(512)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_photos_taken_at", "photos", ["taken_at"])


def downgrade() -> None:
    op.drop_index("ix_photos_taken_at", table_name="photos")
    op.drop_table("photos")
    # The vector extension is left in place: other tables may use it later.
