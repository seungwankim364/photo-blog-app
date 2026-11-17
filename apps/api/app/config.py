from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All settings come from environment variables, so local and EKS differ only by config."""

    database_url: str = "postgresql+psycopg://photoblog:photoblog@localhost:5432/photoblog"


settings = Settings()
