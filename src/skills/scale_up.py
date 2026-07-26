"""Skill: Escalar horizontalmente un servicio ECS."""

import logging

from langchain_core.tools import tool

from src.infrastructure.clients import aws_clients

logger = logging.getLogger(__name__)

# ECS Cluster name (configurable via env)
ECS_CLUSTER = "kiro-monitor-dev-cluster"


@tool
def scale_up(service_name: str, desired_count: int = 3) -> str:
    """Escala horizontalmente un servicio ECS aumentando el número de tareas.

    Args:
        service_name: Nombre del servicio a escalar (ej: user-svc, order-svc)
        desired_count: Número deseado de tareas (default: 3)

    Returns:
        Resultado de la operación de escalado.
    """
    logger.info("Ejecutando scale_up: %s -> %d tareas", service_name, desired_count)

    try:
        response = aws_clients.ecs.update_service(
            cluster=ECS_CLUSTER,
            service=service_name,
            desiredCount=desired_count,
        )

        service_status = response.get("service", {}).get("status", "UNKNOWN")
        logger.info("Servicio %s escalado a %d tareas. Status: %s", service_name, desired_count, service_status)

        return f"Servicio '{service_name}' escalado a {desired_count} tareas exitosamente. Status: {service_status}"

    except Exception as e:
        logger.error("Error al escalar servicio %s: %s", service_name, str(e))
        return f"Error al escalar '{service_name}': {str(e)}"
