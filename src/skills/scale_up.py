"""Skill: Escalar horizontalmente un servicio ECS."""

import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


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

    # TODO: Implementar con boto3
    # ecs_client.update_service(
    #     cluster="kiro-cluster",
    #     service=service_name,
    #     desiredCount=desired_count
    # )

    return f"Servicio '{service_name}' escalado a {desired_count} tareas."
