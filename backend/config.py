from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_ignore_empty=True
    )

    POSTGRES_USER: str = "carlog"
    POSTGRES_PASSWORD: str = "carlog123"
    POSTGRES_DB: str = "carlog"
    DATABASE_URL: str = "postgresql://carlog:carlog123@localhost:5432/carlog"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    JWT_SECRET: str = "secret"
    TOKEN_TTL_MIN: int = 60


config = Config()
