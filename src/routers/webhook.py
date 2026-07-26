"""Webhook Router - Endpoint para recibir alertas de CloudWatch."""

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


@router.post(
    "/test",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Endpoint de prueba para simular una alerta",
)
async def test_alert() -> WebhookResponse:
    """Endpoint de prueba para simular una alerta sin necesidad de CloudWatch."""
    test_alert_data = CloudWatchAlert(
        alarm_name="test-high-cpu",
        state="ALARM",
        reason="CPU utilization exceeded 80% threshold",
        namespace="AWS/ECS",
        metric_name="CPUUtilization",
        dimensions={"ServiceName": "payment-service", "ClusterName": "kiro-monitor-dev-cluster"},
        raw_payload={
            "error_type": "DatabaseTimeoutError",
            "status_code": 503,
            "duration_ms": 3500,
            "message": "Connection timeout acquiring connection from pool",
        },
    )

    logger.info("Test alerta simulada: %s", test_alert_data.alarm_name)
    response = await analyze_alert(test_alert_data)
    return response


@router.post(
    "/chaos",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Simula un incidente de chaos engineering",
)
async def chaos_alert(service: str = "payment-service", error_type: str = "DatabaseTimeoutError") -> WebhookResponse:
    """Simula un incidente de chaos engineering para probar el agente."""
    from src.models.alerts import CloudWatchAlert

    error_mapping = {
        "DatabaseTimeoutError": {"status_code": 503, "duration_ms": 5000},
        "PaymentGatewayTimeoutError": {"status_code": 504, "duration_ms": 4500},
        "BiometricServiceFailure": {"status_code": 500, "duration_ms": 2000},
        "InventoryLockError": {"status_code": 500, "duration_ms": 3000},
        "InternalServerError": {"status_code": 500, "duration_ms": 1500},
    }

    error_info = error_mapping.get(error_type, {"status_code": 500, "duration_ms": 2000})

    alert_data = CloudWatchAlert(
        alarm_name=f"chaos-{error_type.lower()}-{service}",
        state="ALARM",
        reason=f"Simulated {error_type} in {service}",
        namespace="AWS/ECS",
        metric_name="ErrorCount",
        dimensions={"ServiceName": service, "ClusterName": "kiro-monitor-dev-cluster"},
        raw_payload={
            "error_type": error_type,
            "status_code": error_info["status_code"],
            "duration_ms": error_info["duration_ms"],
            "message": f"Simulated {error_type}",
        },
    )

    logger.info("Chaos alerta simulada: %s", alert_data.alarm_name)
    response = await analyze_alert(alert_data)
    return response
