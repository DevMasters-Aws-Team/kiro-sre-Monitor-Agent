"""Proveedor de LLM para uso fuera de create_agent (si se necesita).

El Agente SRE Autónomo usa create_agent directamente con model_provider="bedrock_converse".
Este módulo queda disponible para otros usos que requieran el LLM directamente.
"""

import logging

from langchain_core.language_models import BaseChatModel

from src.config import settings

logger = logging.getLogger(__name__)


def get_llm() -> BaseChatModel:
    """Retorna la instancia del LLM de Bedrock."""
    from langchain_aws import ChatBedrock

    logger.info("Conectando a Bedrock: %s", settings.bedrock_model_id)

    return ChatBedrock(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
        model_kwargs={
            "temperature": 0.1,
            "max_tokens": 2048,
        },
    )
