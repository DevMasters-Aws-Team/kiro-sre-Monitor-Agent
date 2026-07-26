"""Skill: Reiniciar un servicio ECS."""

import logging

from langchain_core.tools import tool

from src.infrastructure.clients import aws_clients

logger = logging.getLogger(__name__)

# ECS Cluster name (configurable via env)
ECS_CLUSTER = "kiro-monitor-dev-cluster"


@tool
def restart_service(service_name: str) -> str:
    """Reinicia un servicio ECS forzando un nuevo deployment.

    Args:
        service_name: Nombre del servicio a reiniciar (ej: user-svc, order-svc)

    Returns:
        Resultado de la operación de reinicio.
    """
    logger.info("Ejecutando restart_service: %s", service_name)

    try:
        response = aws_clients.ecs.update_service(
            cluster=ECS_CLUSTER,
            service=service_name,
            forceNewDeployment=True,
        )

        service_status = response.get("service", {}).get("status", "UNKNOWN")
        logger.info("Servicio %s reiniciado. Status: %s", service_name, service_status)

        return f"Servicio '{service_name}' reiniciado exitosamente. Nuevo deployment en progreso. Status: {service_status}"

    except Exception as e:
        logger.error("Error al reiniciar servicio %s: %s", service_name, str(e))
        return f"Error al reiniciar '{service_name}': {str(e)}"
