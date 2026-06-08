from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://omnitick:omnitick_dev@localhost:5432/omnitick"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    imap_poll_interval: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
