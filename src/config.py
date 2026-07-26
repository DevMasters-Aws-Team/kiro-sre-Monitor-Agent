from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración del agente orquestador."""

    app_name: str = "kiro-sre-monitor-agent"
    environment: str = "dev"
    debug: bool = False

    # AWS Credentials
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None

    # AWS Config
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "us.amazon.nova-lite-v1:0"  # Amazon Nova Lite
    use_mock_aws: bool = True  # Default: True para desarrollo local

    # CloudWatch Logs (debe coincidir con LOG_GROUP_NAME del Backend)
    log_group_name: str = "/kiro/microservices/backend"

    # DynamoDB
    knowledge_table: str = "KnowledgeTable"
    tickets_table: str = "TicketsTable"
    incidents_table: str = "IncidentsTable"
    audit_table: str = "AuditTable"

    # Persistencia opcional: si las tablas DynamoDB no existen, el agente
    # sigue funcionando pero no guarda audit trail.
    enable_audit_trail: bool = True

    # EventBridge
    event_bus_name: str = "kiro-monitor-events"

    model_config = {"env_file": ".env", "env_prefix": "KIRO_"}


settings = Settings()
