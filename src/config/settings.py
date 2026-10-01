import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _frontend_origins():
    configured = os.getenv("FRONTEND_ORIGINS")
    if configured:
        return tuple(
            origin.strip()
            for origin in configured.split(",")
            if origin.strip()
        )

    return (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )


@dataclass(frozen=True)
class Settings:
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "cloud_optimizer")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "")
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    frontend_origins: tuple[str, ...] = _frontend_origins()


settings = Settings()