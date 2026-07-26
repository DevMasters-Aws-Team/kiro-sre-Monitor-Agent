"""Alerts Router - Endpoint for frontend alerts dashboard."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Alerts"])


class AlertIncident(BaseModel):
    """Alert incident model for frontend."""
    id: str
    title: str
    service: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    timestamp: str


# Initial alerts data matching frontend expectations
ALERTS = [
    AlertIncident(
        id="alt-01",
        title="Incidencia Crítica: Ventas (sales-service)",
        service="sales-service",
        severity="CRITICAL",
        description="Timeout de conexión DB en DynamoDB. Error HTTP 500 recurrente en registros de transacciones.",
        timestamp="Hace 10m",
    ),
]


@router.get("/api/alerts")
async def get_alerts() -> list[dict]:
    """Returns list of alert incidents for the frontend dashboard."""
    return [alert.model_dump() for alert in ALERTS]


@router.post("/api/alerts")
async def create_alert(alert: AlertIncident) -> dict:
    """Creates a new alert incident."""
    ALERTS.append(alert)
    return {"status": "created", "alert": alert.model_dump()}
