from sqlalchemy.engine import URL

from src.config.settings import settings

DB_CONFIG = {
    "host": settings.db_host,
    "port": settings.db_port,
    "database": settings.db_name,
    "user": settings.db_user,
    "password": settings.db_password,
}

API_HOST = settings.api_host
API_PORT = settings.api_port
FRONTEND_ORIGINS = settings.frontend_origins


def get_database_url():
    return URL.create(
        "postgresql+psycopg2",
        username=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
    )