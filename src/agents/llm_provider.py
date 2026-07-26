"""Proveedor de LLM multi-cloud.

Resuelve el modelo configurado en KIRO_MODEL_ID soportando:
  - ollama:model           → Ollama local (dev)
  - openai:model           → OpenAI API
  - azure_openai:model     → Azure OpenAI (Azure AD o API key)
  - bedrock_converse:model → AWS Bedrock
  - google_genai:model     → Google AI (Gemini)
  - google_vertexai:model  → Google Vertex AI
  - anthropic:model        → Anthropic Claude directo
  - fireworks:model        → Fireworks AI
  - groq:model             → Groq

Para providers que usan API key estándar (openai, anthropic, fireworks, groq, google_genai),
basta con configurar la variable de entorno del proveedor (OPENAI_API_KEY, etc.)
y create_agent lo resuelve automáticamente.

Para Azure OpenAI con Azure AD (sin API key), se instancia manualmente con
DefaultAzureCredential para usar la sesión de 'az login'.
"""

import logging

from langchain_core.language_models import BaseChatModel

from src.config import settings

logger = logging.getLogger(__name__)


def get_model() -> BaseChatModel | str:
    """Resuelve el modelo LLM según el provider configurado.

    Returns:
        BaseChatModel (si requiere instanciación manual) o string de modelo
        compatible con create_agent / init_chat_model.
    """
    model_id = settings.model_id
    provider = model_id.split(":")[0] if ":" in model_id else ""
    model_name = model_id.split(":", 1)[1] if ":" in model_id else model_id

    logger.info("Resolviendo modelo: provider=%s, model=%s", provider, model_name)

    # ── Azure OpenAI con Azure AD ───────────────────────────────────────
    if provider == "azure_openai" and settings.azure_use_ad:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        from langchain_openai import AzureChatOpenAI

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )

        deployment = settings.azure_deployment or model_name

        logger.info("Usando Azure OpenAI con Azure AD: deployment=%s", deployment)
        return AzureChatOpenAI(
            azure_deployment=deployment,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            azure_ad_token_provider=token_provider,
            temperature=0,
        )

    # ── Todos los demás providers ───────────────────────────────────────
    # create_agent / init_chat_model resuelve automáticamente usando las
    # variables de entorno estándar de cada proveedor:
    #   - openai          → OPENAI_API_KEY
    #   - azure_openai    → AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT
    #   - bedrock_converse→ AWS credentials (aws configure)
    #   - google_genai    → GOOGLE_API_KEY
    #   - google_vertexai → GOOGLE_APPLICATION_CREDENTIALS o gcloud auth
    #   - anthropic       → ANTHROPIC_API_KEY
    #   - ollama          → (sin auth, solo necesita ollama corriendo)
    #   - fireworks       → FIREWORKS_API_KEY
    #   - groq            → GROQ_API_KEY
    logger.info("Usando provider '%s' via init_chat_model", provider)
    return model_id
