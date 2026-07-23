"""Skill: Limpiar cache Redis de un servicio."""

import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def clear_cache(service_name: str) -> str:
    """Limpia el cache Redis asociado a un servicio específico.

    Args:
        service_name: Nombre del servicio cuyo cache se debe limpiar (ej: user-svc, auth-svc)

    Returns:
        Resultado de la operación de limpieza.
    """
    logger.info("Ejecutando clear_cache: %s", service_name)

    # TODO: Implementar con redis client
    # redis_client.delete(f"{service_name}:*")

    return f"Cache de '{service_name}' limpiado exitosamente."
