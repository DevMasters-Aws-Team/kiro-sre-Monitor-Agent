from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración del agente orquestador.

    Soporta múltiples proveedores de modelo:
      - ollama:modelo           → Ollama local (dev)
      - openai:modelo           → OpenAI API
      - azure_openai:modelo     → Azure OpenAI (con API key o Azure AD)
      - bedrock_converse:modelo → AWS Bedrock
      - google_genai:modelo     → Google AI (Gemini)
      - google_vertexai:modelo  → Google Vertex AI

    Para azure_openai con Azure AD (sin API key), configurar:
      - azure_openai_endpoint
      - azure_deployment
      - azure_use_ad = true

    Para los demás proveedores, basta con el model_id y las variables
    de entorno estándar del proveedor (OPENAI_API_KEY, etc.).
    """

    app_name: str = "kiro-sre-monitor-agent"
    environment: str = "dev"
    debug: bool = False

    # ── Modelo LLM ──────────────────────────────────────────────────────
    # Formato: "provider:model_name"
    # Ejemplos:
    #   ollama:qwen3:8b
    #   openai:gpt-4o
    #   azure_openai:gpt-5.4-nano
    #   bedrock_converse:anthropic.claude-3-sonnet-20240229-v1:0
    #   google_genai:gemini-2.0-flash
    #   google_vertexai:gemini-2.0-flash
    model_id: str = "azure_openai:gpt-5.4-nano"

    # ── Azure OpenAI ────────────────────────────────────────────────────
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-12-01-preview"
    azure_deployment: str = ""
    azure_use_ad: bool = True  # True = usa Azure AD (az login), False = usa API key

    # ── AWS ─────────────────────────────────────────────────────────────
    aws_region: str = "us-east-1"

    # ── Google Vertex AI ────────────────────────────────────────────────
    gcp_project: str = ""
    gcp_location: str = "us-central1"

    # ── DynamoDB ────────────────────────────────────────────────────────
    knowledge_table: str = "KnowledgeTable"
    tickets_table: str = "TicketsTable"
    incidents_table: str = "IncidentsTable"
    audit_table: str = "AuditTable"

    # ── EventBridge ─────────────────────────────────────────────────────
    event_bus_name: str = "kiro-monitor-events"

    model_config = {"env_file": ".env", "env_prefix": "KIRO_", "extra": "ignore"}


settings = Settings()
