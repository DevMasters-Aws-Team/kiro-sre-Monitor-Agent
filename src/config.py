from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración del agente orquestador."""

    app_name: str = "kiro-sre-monitor-agent"
    environment: str = "dev"
    debug: bool = False

    # AWS
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"

    # DynamoDB
    knowledge_table: str = "KnowledgeTable"
    tickets_table: str = "TicketsTable"
    incidents_table: str = "IncidentsTable"
    audit_table: str = "AuditTable"

    # EventBridge
    event_bus_name: str = "kiro-monitor-events"

    model_config = {"env_file": ".env", "env_prefix": "KIRO_"}


settings = Settings()
