"""Skill: Limpiar cache Redis de un servicio."""

import logging

from langchain_core.tools import tool

from src.infrastructure.clients import aws_clients

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

    try:
        # Pattern to match cache keys for this service
        pattern = f"{service_name}:*"

        # For ElastiCache, we'd use a different approach
        # For now, we'll use the mock/simple implementation
        deleted_count = aws_clients.elasticache.delete(pattern)

        logger.info("Cache de %s limpiado. Keys eliminadas: %d", service_name, deleted_count)

        return f"Cache de '{service_name}' limpiado exitosamente. {deleted_count} keys eliminadas."

    except Exception as e:
        logger.error("Error al limpiar cache de %s: %s", service_name, str(e))
        return f"Error al limpiar cache de '{service_name}': {str(e)}"
