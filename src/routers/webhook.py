import logging

from fastapi import APIRouter, status

from src.agents.sre_autonomo import analyze_alert
from src.models.alerts import CloudWatchAlert, WebhookResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.post(
    "",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Recibe alertas de CloudWatch para análisis del agente",
)
async def receive_alert(alert: CloudWatchAlert) -> WebhookResponse:
    """Endpoint que recibe alertas de CloudWatch/SNS y las pasa al agente para análisis."""
    logger.info("Webhook recibido: %s", alert.alarm_name)
    response = await analyze_alert(alert)
    return response
