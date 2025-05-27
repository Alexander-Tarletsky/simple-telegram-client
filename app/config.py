import logging
import pathlib

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, EmailStr, field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

# https://github.com/pydantic/pydantic/issues/1368
# https://docs.pydantic.dev/usage/settings/#dotenv-env-support
load_dotenv()

logger = logging.getLogger(__name__)

BASE_ROOT = pathlib.Path(__file__).resolve().parent


class Settings(BaseSettings):
    DEBUG: bool = False
    PYTHONASYNCIODEBUG: bool = False

    TEST_MODE: bool = False

    ENVIRONMENT: str = "development"
    IS_PRODUCTION: bool = False
    IS_DEVELOPMENT: bool = True
    IS_LOCAL: bool = False

    LOG_LEVEL: str = "INFO"

    @field_validator("ENVIRONMENT", mode="before")
    def set_environment(cls, value: str) -> str:  # NOQA: N805
        if value not in ("development", "production", "local"):
            raise ValueError("Invalid environment")
        return value

    @field_validator("IS_PRODUCTION", mode="before")
    def set_is_production(cls, value: bool, info: ValidationInfo) -> bool:  # NOQA: N805
        return info.data.get("ENVIRONMENT") == "production"

    @field_validator("IS_DEVELOPMENT", mode="before")
    def set_is_development(cls, value: bool, info: ValidationInfo) -> bool:  # NOQA: N805
        return info.data.get("ENVIRONMENT") == "development"

    @field_validator("IS_LOCAL", mode="before")
    def set_is_local(cls, value: bool, info: ValidationInfo) -> bool:  # NOQA: N805
        return info.data.get("ENVIRONMENT") == "local"

    FIRST_SUPERUSER: EmailStr = "root@root.com"
    FIRST_SUPERUSER_PW: str = "strongpassword"

    BASE_HOST: AnyHttpUrl = "http://localhost:8000"
    API_V1_STR: str = "/api/v1"

    TG_API_ID: int = 123456  # Replace with your actual Telegram API ID
    TG_API_HASH: str = "your_api_hash_here"  # Replace with your actual Telegram API hash

    ENCRYPTION_KEY: str = "your_encryption_key_here"  # Key for encrypting session data

    API_KEY: str = "your_api_key_here"  # Own API key to access the API

    MAIN_SERVICE_URL: AnyHttpUrl = "http://localhost:8000"  # URL to the main service
    MAIN_SERVICE_API_KEY: str = "your_main_service_api_key_here"  # API key for the main service

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = [
        "http://localhost",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:  # NOQA: N805
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list | str):
            return v
        raise ValueError(v)

    @field_validator("ENCRYPTION_KEY", mode="before")
    def assemble_encryption_key(cls, value: str | None) -> str:  # NOQA: N805
        if not value:
            raise ValueError("ENCRYPTION_KEY must be set")
        return value

    @field_validator("DEBUG", "TEST_MODE", "PYTHONASYNCIODEBUG", mode="before")
    def assemble_bool(cls, value: str | int | bool | None) -> bool:  # NOQA: N805
        return bool(value)

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file="./.env",
        env_file_encoding="utf-8",
    )


settings = Settings()
