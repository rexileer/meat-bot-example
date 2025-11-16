from pydantic.v1 import BaseSettings
from pathlib import Path

from data.constants import DATA_DIR

app_dir: Path = Path(__file__).parent.parent
class Settings(BaseSettings):
    APP_DIR=app_dir
    POSTGRES_SERVER: str
    POSTGRES_PORT: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    TELEGRAM_BOT_TOKEN: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    MINIO_ENDPOINT: str
    MINIO_USE_HTTPS: bool
    MINIO_MAIN_BUCKET: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str

    ADMIN_USER: str
    ADMIN_PASSWORD: str

    LOGIN: str
    HOST: str

    DEVELOPER: int

    class Config:
        env_file = f"{DATA_DIR}/.env"
        env_file_encoding = "utf-8"
        case_sensitive = True
env = Settings()
