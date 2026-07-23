from fastapi import FastAPI

from src.config import settings
from src.routers.registry import register_routers

app = FastAPI(
    title=settings.app_name,
    description="Kiro SRE Agent - Plataforma de creación de agentes inteligentes",
    version="0.1.0",
)

register_routers(app)
