"""Event Handler - Handler para eventos de EventBridge."""

import json
import logging
from typing import Any

from src.agents.orchestrator import orchestrator
from src.models.alerts import CloudWatchAlert

logger = logging.getLogger(__name__)


class EventBridgeHandler:
    """Handler para eventos de EventBridge."""

    def __init__(self):
        self.orchestrator = orchestrator

    async def handle_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Maneja un evento de EventBridge."""
        logger.info("Evento recibido: %s", json.dumps(event, indent=2))

        try:
            # Determinar el tipo de evento
            source = event.get("source", "")
            detail_type = event.get("detail-type", "")
            detail = event.get("detail", {})

            if source == "aws.cloudwatch" and "CloudWatch Alarm" in detail_type:
                return await self._handle_cloudwatch_alarm(detail)
            elif source == "aws.ecs" and "ECS Task State Change" in detail_type:
                return await self._handle_ecs_task_change(detail)
            elif source == "kiro.microservices" and detail_type == "ApplicationError":
                return await self._handle_application_error(detail)
            else:
                logger.warning("Evento desconocido: source=%s, detail-type=%s", source, detail_type)
                return {"status": "ignored", "reason": "Evento no soportado"}

        except Exception as e:
            logger.error("Error procesando evento: %s", str(e))
            return {"status": "error", "error": str(e)}

    async def _handle_cloudwatch_alarm(self, detail: dict) -> dict[str, Any]:
        """Maneja un evento de cambio de estado de alarma de CloudWatch."""
        alarm_name = detail.get("alarmName", "")
        state = detail.get("state", {})
        state_value = state.get("value", "")
        reason = state.get("reason", "")

        logger.info(
            "Alarma CloudWatch: %s → %s (%s)",
            alarm_name,
            state_value,
            reason,
        )

        # Crear alerta para el orquestador
        alert = CloudWatchAlert(
            alarm_name=alarm_name,
            state=state_value,
            reason=reason,
            namespace=detail.get("namespace", "AWS/ECS"),
            dimensions=detail.get("dimensions", {}),
            raw_payload=detail,
        )

        # Procesar con el orquestador
        response = await self.orchestrator.process_alert(alert)

        return {
            "status": "processed",
            "alert_id": response.alert_id,
            "analysis": response.analysis,
        }

    async def _handle_ecs_task_change(self, detail: dict) -> dict[str, Any]:
        """Maneja un evento de cambio de estado de tarea ECS."""
        task_arn = detail.get("taskArn", "")
        service_name = detail.get("clusterArn", "").split("/")[-1]
        last_status = detail.get("lastStatus", "")
        stopped_reason = detail.get("stoppedReason", "")

        logger.info(
            "Tarea ECS cambió: %s → %s (%s)",
            task_arn,
            last_status,
            stopped_reason,
        )

        # Si la tarea se detuvo inesperadamente, crear alerta
        if last_status == "STOPPED" and stopped_reason:
            alert = CloudWatchAlert(
                alarm_name=f"ecs-task-stopped-{service_name}",
                state="ALARM",
                reason=stopped_reason,
                namespace="AWS/ECS",
                dimensions={
                    "ServiceName": service_name,
                    "TaskArn": task_arn,
                },
                raw_payload=detail,
            )

            response = await self.orchestrator.process_alert(alert)

            return {
                "status": "processed",
                "alert_id": response.alert_id,
                "analysis": response.analysis,
            }

        return {"status": "ignored", "reason": f"Tarea en estado: {last_status}"}

    async def _handle_application_error(self, detail: dict) -> dict[str, Any]:
        """Maneja un evento de error de aplicación personalizado."""
        service = detail.get("service", "unknown")
        error_type = detail.get("errorType", "UnknownError")
        message = detail.get("message", "")
        status_code = detail.get("statusCode", 500)

        logger.info(
            "Error de aplicación: %s en %s (status=%d)",
            error_type,
            service,
            status_code,
        )

        alert = CloudWatchAlert(
            alarm_name=f"app-error-{service}",
            state="ALARM",
            reason=message,
            namespace="Application",
            dimensions={"ServiceName": service},
            raw_payload=detail,
        )

        response = await self.orchestrator.process_alert(alert)

        return {
            "status": "processed",
            "alert_id": response.alert_id,
            "analysis": response.analysis,
        }


# Singleton instance
event_handler = EventBridgeHandler()
