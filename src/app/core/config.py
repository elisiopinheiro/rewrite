"""Application settings loaded from environment variables."""

from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Application
    APP_VERSION: str = "development"
    APP_ENVIRONMENT: Literal["dev", "int", "prod"] = "dev"

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "clusters"
    DB_USERNAME: str = "cluster_app"
    DB_PASSWORD: str = "password"
    DATABASE_LOGGING_LEVEL: Literal["DEBUG", "INFO", "WARN", "ERROR"] = "WARN"

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.DB_USERNAME,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )

    # Authentication — M4W
    BASIC_API_USERNAME: str = "4wm"
    BASIC_API_PASSWORD: str = "4wm"

    # Authentication — Partners
    BASIC_M4W_API_USERNAME: str = "ctw"
    BASIC_M4W_API_PASSWORD: str = "ctw"
    BASIC_CLOUD_API_USERNAME: str = "cloud"
    BASIC_CLOUD_API_PASSWORD: str = "cloud"
    BASIC_SCP_API_USERNAME: str = "scp"
    BASIC_SCP_API_PASSWORD: str = "scp"
    BASIC_SOLAR_API_USERNAME: str = "solar"
    BASIC_SOLAR_API_PASSWORD: str = "solar"

    # Validation
    ADGR_GROUP_REGEX: str = r"^(APPL_|RN-|RN_).*$"

    @field_validator("ADGR_GROUP_REGEX", mode="before")
    @classmethod
    def normalize_adgr_group_regex(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip('"')
        return value


settings = Settings()
