from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CloudWatchAlert(BaseModel):
    """Modelo de alerta recibida desde CloudWatch/SNS."""

    alarm_name: str = Field(..., description="Nombre de la alarma de CloudWatch")
    alarm_description: str | None = Field(None, description="Descripción de la alarma")
    state: str = Field(..., description="Estado de la alarma (ALARM, OK, INSUFFICIENT_DATA)")
    previous_state: str | None = Field(None, description="Estado anterior")
    reason: str = Field(..., description="Razón del cambio de estado")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    region: str = Field(default="us-east-1")
    namespace: str | None = Field(None, description="Namespace de la métrica (AWS/ECS, etc.)")
    metric_name: str | None = Field(None, description="Nombre de la métrica")
    dimensions: dict[str, str] = Field(default_factory=dict)
    raw_payload: dict[str, Any] = Field(default_factory=dict, description="Payload original completo")


class WebhookResponse(BaseModel):
    """Respuesta del webhook tras procesar la alerta."""

    status: str = Field(..., description="Estado del procesamiento")
    alert_id: str = Field(..., description="ID asignado a la alerta")
    analysis: str | None = Field(None, description="Análisis inicial del agente")
    actions_suggested: list[str] = Field(default_factory=list)
