"""Skill: Purgar mensajes de una cola SQS."""

import logging

from langchain_core.tools import tool

from src.infrastructure.clients import aws_clients

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

    try:
        # Construct queue URL (in real implementation, you'd look this up)
        queue_url = f"https://sqs.us-east-1.amazonaws.com/123456789012/{queue_name}"

        aws_clients.sqs.purge_queue(QueueUrl=queue_url)

        logger.info("Cola %s purgada exitosamente", queue_name)

        return f"Cola '{queue_name}' purgada exitosamente. Todos los mensajes eliminados."

    except Exception as e:
        logger.error("Error al purgar cola %s: %s", queue_name, str(e))
        return f"Error al purgar cola '{queue_name}': {str(e)}"
