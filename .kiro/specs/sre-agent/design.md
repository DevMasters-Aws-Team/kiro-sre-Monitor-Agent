# Design — Kiro SRE Monitor Agent (Carmen)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Kiro SRE Agent — Carmen (port 8001)                │
│                                                                     │
│  POST /webhook ──▶ sre_autonomo/agent.py ──▶ orchestrator.py       │
│                         │                                           │
│            ┌────────────┼────────────┬──────────────┐              │
│            ▼            ▼            ▼              ▼              │
│     CloudWatch      DynamoDB      Bedrock      Decision            │
│     (OBSERVE)       (KB lookup)   (REASON)     Engine              │
│            │            │            │         (fallback)          │
│            └────────────┴────────────┘                             │
│                         │                                           │
│                  Decision Engine                                    │
│                  confidence → action → skill                       │
│                         │                                           │
│         ┌───────────────┼───────────────┐                          │
│         ▼               ▼               ▼                          │
│  restart_service    scale_up        clear_cache   purge_queue      │
│  (@tool LangChain)  (@tool)         (@tool)       (@tool)          │
│         │                                                           │
│         ▼                                                           │
│  DynamoDB AuditTable (ACT + log)                                   │
│                                                                     │
│  GET /health    POST /chat    GET /skills    GET /incidents         │
└─────────────────────────────────────────────────────────────────────┘
              │                        │
              ▼                        ▼
     Backend :8000               Kiro IDE Local
     (fallback logs)             (.kiro/settings/mcp.json)
                                  ├── kiro-cloudwatch MCP
                                  ├── kiro-dynamodb MCP
                                  └── aws-docs MCP (uvx)
```

## Component Design

### Orchestrator (`src/agents/orchestrator.py`)

Implementa el ciclo **Observe → Reason → Act**:

```
process_alert(alert: CloudWatchAlert)
├── OBSERVE: _observe(alert)
│   ├── aws_clients.cloudwatch_logs.filter_log_events()
│   └── Fallback: httpx GET /api/logs del Backend local
├── REASON: _reason(alert, context)
│   ├── Si KIRO_USE_MOCK_AWS=false → _reason_with_llm() [Bedrock]
│   └── Fallback: decision_engine.diagnose() [reglas]
└── ACT: _act(decision)
    ├── Si auto-ejecutable → _invoke_skill(skill_name, params)
    ├── Si requiere confirmación → retorna pending
    └── Si escalar → retorna escalate
```

### Decision Engine (`src/agents/decision_engine.py`)

Motor de reglas determinístico que sirve como fallback cuando Bedrock no está disponible:

| Error Type | Action | Risk | Confidence |
|-----------|--------|------|-----------|
| DatabaseTimeoutError | restart_service | medium | 0.85 |
| PaymentGatewayTimeoutError | restart_service | medium | 0.80 |
| BiometricServiceFailure | clear_cache | low | 0.75 |
| InventoryLockError | purge_queue | medium | 0.70 |
| InternalServerError | restart_service | medium | 0.60 |

### Skills — LangChain `@tool` decorators

```python
@tool
def restart_service(service_name: str) -> str:
    """Reinicia un servicio ECS forzando nuevo deployment."""
    aws_clients.ecs.update_service(cluster=ECS_CLUSTER, service=service_name,
                                   forceNewDeployment=True)
```

Las 4 skills están registradas en el catálogo `GET /skills` con:
- `risk_level`, `requires_confirmation`, `iam_permissions`
- `trigger_conditions`, `example_params`
- `implemented: true`, `langchain_tool: true`

### MCP Servers (`src/mcp/`)

| Servidor | Herramientas | Uso |
|----------|-------------|-----|
| `kiro-cloudwatch` | `get_recent_errors`, `get_service_health`, `get_incident_summary` | Kiro IDE local |
| `kiro-dynamodb` | `query_knowledge_base`, `list_known_errors` | Kiro IDE local |
| `aws-docs` (uvx) | `search_documentation`, `read_documentation` | Kiro IDE local |

Los MCP servers usan protocolo JSON-RPC 2.0 via stdio y se configuran en `.kiro/settings/mcp.json`.

### Incident History (en memoria)

El orquestador mantiene un `deque(maxlen=50)` con los últimos 50 incidentes analizados. Esto permite que el chat de Carmen responda preguntas contextualizadas como "¿qué pasó con sales-service?" sin necesidad de consultar DynamoDB.

```python
INCIDENT_HISTORY: deque = deque(maxlen=50)

get_incident_summary() → {"total", "services_affected", "by_error_type", "critical_count"}
get_recent_incidents(limit) → [{"service", "error_type", "root_cause", "decision", ...}]
```

## API Endpoints

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/webhook` | Recibe alertas del Backend | No |
| POST | `/webhook/test` | Simula alerta de prueba | No |
| POST | `/webhook/chaos` | Simula fallo controlado | No |
| POST | `/chat` | Chat con Carmen (Bedrock) | No |
| POST | `/chat/test` | Verifica conexión Bedrock | No |
| GET | `/incidents` | Historial de incidentes en sesión | No |
| GET | `/skills` | Catálogo de skills con metadata | No |
| POST | `/skills/{name}` | Invocar skill directamente | No |
| GET | `/health` | Health check | No |

## AWS Infrastructure (Terraform)

| Recurso | Nombre | Propósito |
|---------|--------|-----------|
| DynamoDB | `kiro-dev-KnowledgeTable` | Errores conocidos + soluciones |
| DynamoDB | `kiro-dev-TicketsTable` | Tickets de incidentes |
| DynamoDB | `kiro-dev-IncidentsTable` | Historial persistente |
| EventBridge | `kiro-monitor-events` | Bus de eventos AWS |
| Lambda | `kiro-dev-agent` | Orquestador serverless |
| CloudWatch | `/kiro/microservices/backend` | Log group del Backend |
| Cognito | `kiro-dashboard-users` | Auth del dashboard |
| SNS | `kiro-dev-incidents` | Alertas por email |
| S3 | Terraform state | Backend Terraform |

## Deployment

| Entorno | Plataforma | Puerto | URL |
|---------|-----------|--------|-----|
| Local dev | `uvicorn --reload` | 8001 | `http://localhost:8001` |
| Producción | EC2 + Docker | 8001 | EC2 Public IP |

## Testing Strategy

| Archivo | Qué prueba |
|---------|-----------|
| `test_decision_engine.py` | Clasificación de severidad y selección de acción |
| `test_event_handler.py` | Parsing de eventos EventBridge y schema CloudWatchAlert |
| `test_orchestrator.py` | Ciclo completo Observe→Reason→Act con mocks AWS |
| `test_skills.py` | Ejecución de cada skill con MockECS/MockSQS |
| `test_webhook.py` | Endpoints /webhook, /webhook/test, /webhook/chaos |
| `test_sre_autonomo.py` | Integración end-to-end del agente |
| `test_health.py` | Health check endpoint |
