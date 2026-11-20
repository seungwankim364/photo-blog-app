from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All settings come from environment variables, so local and EKS differ only by config."""

    database_url: str = "postgresql+psycopg://photoblog:photoblog@localhost:5432/photoblog"

    # Where uploaded originals are saved in Phase 0. Replaced by S3 later.
    upload_dir: str = "./uploads"
    max_upload_mb: int = 30

    # Cameras often write the time without a timezone. This one is assumed then.
    exif_default_tz: str = "Asia/Seoul"


settings = Settings()
