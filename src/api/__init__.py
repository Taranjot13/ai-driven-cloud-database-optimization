import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import router
from src.config.settings import settings


def create_app():
    application = FastAPI(
        title="Database Optimization API",
        version="1.0.0",
        description=(
            "Read-only observability and explicitly authorized "
            "optimization actions for the PostgreSQL prototype."
        ),
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.frontend_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @application.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request,
        error: Exception,
    ):
        logging.getLogger("database_api").exception(
            "Unhandled API error on %s",
            request.url.path,
            exc_info=error,
        )
        return JSONResponse(
            status_code=503,
            content={
                "detail": (
                    "The requested data is temporarily unavailable. "
                    "Check the API and database connection, then retry."
                )
            },
        )

    application.include_router(router, prefix="/api")
    return application


app = create_app()