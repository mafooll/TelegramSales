from pathlib import Path
from typing import ClassVar

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

ROOT_PATH = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT_PATH / ".env"
LOCALES_PATH = Path(__file__).resolve().parents[3] / "locales"


class BotSettings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="BOT_",
        extra="ignore",
    )

    token: SecretStr
    drop_pending_updates: bool = True


class PostgresSettings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="POSTGRES_",
        extra="ignore",
    )

    user: str = "postgres"
    password: SecretStr = SecretStr("postgres")
    db: str = "postgres"
    host: str = "postgres"
    port: int = 5432
    driver: str = "postgresql+asyncpg"

    @property
    def sqlalchemy_url(self) -> URL:
        return URL.create(
            drivername=self.driver,
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.db,
        )

    @property
    def url(self) -> str:
        return self.sqlalchemy_url.render_as_string(hide_password=False)


class RedisSettings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="REDIS_",
        extra="ignore",
    )

    host: str = "redis"
    port: int = 6379
    db: int = 0

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"


class AppSettings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="APP_",
        extra="ignore",
    )

    root_id: int
    work_chat_id: int
    log_level: str = "INFO"
    log_json: bool = False
    log_payloads: bool = True
    log_sql: bool = True
    log_dir: str = "logs"
    log_file_megabytes: int = 10
    log_file_backups: int = 5

    @property
    def log_directory(self) -> Path | None:
        return None if not self.log_dir else ROOT_PATH / self.log_dir
    default_locale: str = "ru"
