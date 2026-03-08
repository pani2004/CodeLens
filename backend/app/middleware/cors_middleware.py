"""CORS middleware configuration."""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()


def add_cors_middleware(app: FastAPI) -> None:
    """Add CORS middleware restricted to the frontend origin."""
    origins = [
        settings.FRONTEND_URL,
    ]
    if settings.ENVIRONMENT == "development":
        origins.extend([
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
        ])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
    )
