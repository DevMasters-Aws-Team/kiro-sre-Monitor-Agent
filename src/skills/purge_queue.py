"""Skill: Purgar mensajes de una cola SQS."""

import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def purge_queue(queue_name: str) -> str:
    """Purga todos los mensajes de una cola SQS.

    Args:
        queue_name: Nombre de la cola SQS a purgar (ej: order-svc-dlq, pay-svc-queue)

    Returns:
        Resultado de la operación de purga.
    """
    logger.info("Ejecutando purge_queue: %s", queue_name)

    # TODO: Implementar con boto3
    # sqs_client.purge_queue(QueueUrl=queue_url)

    return f"Cola '{queue_name}' purgada exitosamente. Todos los mensajes eliminados."
