from fastapi import FastAPI

from src.routers.health import router as health_router
from src.routers.webhook import router as webhook_router


def register_routers(app: FastAPI) -> None:
    """Registra todos los routers en la aplicación FastAPI."""
    app.include_router(health_router)
    app.include_router(webhook_router)
