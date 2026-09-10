from pathlib import Path
from typing import ClassVar

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
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
    root_id: int
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


class AppSettings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="APP_",
        extra="ignore",
    )

    log_level: str = "INFO"
    log_json: bool = False
    default_locale: str = "ru"
