"""Agente SRE Autónomo - Orquestador principal.

Recibe alertas de CloudWatch, las analiza con LangChain create_agent
y ejecuta acciones de remediación cuando es necesario.
"""

import logging

from src.agents.orchestrator import orchestrator
from src.models.alerts import CloudWatchAlert, WebhookResponse

logger = logging.getLogger(__name__)


async def analyze_alert(alert: CloudWatchAlert) -> WebhookResponse:
    """Recibe una alerta de CloudWatch y la analiza con el Agente SRE Autónomo."""
    logger.info(
        "Agente SRE Autónomo procesando alerta: %s | Estado: %s",
        alert.alarm_name,
        alert.state,
    )

    try:
        response = await orchestrator.process_alert(alert)
        return response
    except Exception as e:
        logger.error("Error en el Agente SRE Autónomo: %s", str(e))
        return WebhookResponse(
            status="error",
            alert_id="",
            analysis=f"Error durante el análisis: {str(e)}",
            actions_suggested=[],
        )
