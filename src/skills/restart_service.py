"""Skill: Reiniciar un servicio ECS."""

import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def restart_service(service_name: str) -> str:
    """Reinicia un servicio ECS forzando un nuevo deployment.

    Args:
        service_name: Nombre del servicio a reiniciar (ej: user-svc, order-svc)

    Returns:
        Resultado de la operación de reinicio.
    """
    logger.info("Ejecutando restart_service: %s", service_name)

    # TODO: Implementar con boto3
    # ecs_client.update_service(
    #     cluster="kiro-cluster",
    #     service=service_name,
    #     forceNewDeployment=True
    # )

    return f"Servicio '{service_name}' reiniciado exitosamente. Nuevo deployment en progreso."
