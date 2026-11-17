from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Parent of every table. Alembic reads Base.metadata to know the schema."""
