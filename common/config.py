from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_ignore_empty=True
    )

    DATABASE_URL: str
    JWT_SECRET: str
    TOKEN_TTL_MIN: int = 60
    AUTH_PORT: int = 8001
    LOG_LEVEL: str = "INFO"


config = Config()
