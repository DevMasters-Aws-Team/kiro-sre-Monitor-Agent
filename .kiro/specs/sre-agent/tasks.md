# Tasks — Kiro SRE Monitor Agent (Carmen)

## Task Dependency Graph

```
[1. Core Agent] ──────────────────────────────────────────────┐
[2. Skills + /skills endpoint] ────────────────────────────────┤
[3. MCP Servers] ───────────────────────────────────────────────┤
[4. Hooks] ─────────────────────────────────────────────────────┤
[5. Tests] ─── depends on [1] [2]                              ├──▶ [7. Deploy EC2]
[6. Terraform] ─────────────────────────────────────────────────┘
```

---

- [x] **Task 1: Core Agent (Observe→Reason→Act)**
  - `src/agents/orchestrator.py` — ciclo completo implementado
  - `src/agents/decision_engine.py` — motor de reglas + 5 tipos de error conocidos
  - `src/agents/sre_autonomo/agent.py` — entry point del agente
  - `src/agents/sre_autonomo/prompts.py` — system prompt con análisis de trazas
  - `src/infrastructure/clients.py` — clientes AWS reales + mocks completos
  - `src/models/alerts.py` — schemas Pydantic CloudWatchAlert + WebhookResponse
  - `src/routers/webhook.py` — /webhook, /webhook/test, /webhook/chaos
  - `src/routers/chat.py` — /chat, /chat/test, /incidents con contexto real
  - `src/routers/health.py` — health check

- [x] **Task 2: Skills de Remediación + Catálogo**
  - `src/skills/restart_service.py` — ECS forceNewDeployment (@tool LangChain)
  - `src/skills/scale_up.py` — ECS update desiredCount (@tool LangChain)
  - `src/skills/clear_cache.py` — ElastiCache/Redis key deletion (@tool LangChain)
  - `src/skills/purge_queue.py` — SQS purge (@tool LangChain)
  - `src/routers/skills.py` — GET /skills (catálogo) + POST /skills/{name} (invocar)

- [x] **Task 3: MCP Servers (Kiro IDE)**
  - `src/mcp/cloudwatch_mcp_server.py` — get_recent_errors, get_service_health, get_incident_summary
  - `src/mcp/dynamodb_mcp_server.py` — query_knowledge_base, list_known_errors
  - `.kiro/settings/mcp.json` — registro de 3 servidores MCP: aws-docs, kiro-cloudwatch, kiro-dynamodb

- [x] **Task 4: Hooks de Kiro IDE**
  - `.kiro/hooks/lint-on-save.json` — ruff al guardar .py
  - `.kiro/hooks/run-tests-on-save.json` — pytest al guardar .py
  - `.kiro/hooks/skill-safety-guard.json` — preToolUse: bloquea skills de alto riesgo en prod
  - `.kiro/hooks/webhook-process-log.json` — postToolUse: log estructurado de incidentes

- [x] **Task 5: Test Suite**
  - `tests/conftest.py` + `tests/__init__.py` — fixtures compartidos
  - `tests/test_decision_engine.py` — clasificación y decisión de acciones
  - `tests/test_event_handler.py` — parsing de eventos EventBridge
  - `tests/test_orchestrator.py` — ciclo Observe→Reason→Act completo
  - `tests/test_skills.py` — ejecución de skills con mocks
  - `tests/test_webhook.py` — endpoints webhook
  - `tests/test_sre_autonomo.py` — integración end-to-end
  - `tests/test_health.py` — health check

- [x] **Task 6: Infraestructura Terraform**
  - `terraform/main.tf` — provider + backend S3
  - `terraform/dynamodb.tf` — KnowledgeTable, TicketsTable, IncidentsTable
  - `terraform/lambda.tf` — función kiro-dev-agent
  - `terraform/iam.tf` — roles con Least Privilege
  - `terraform/eventbridge.tf` — event bus + rules
  - `terraform/cloudwatch.tf` — log groups + alarms
  - `terraform/cognito.tf` — user pool para dashboard
  - `terraform/sns.tf` — topics de alertas
  - `terraform/ssm.tf` — Parameter Store para secrets

- [x] **Task 7: Despliegue en Producción**
  - `Dockerfile` — multi-stage build Python 3.12
  - `docker-compose.yml` — orquestación local
  - `.env.example` — template de variables de entorno
  - Desplegado en EC2 puerto 8001
  - Conectado a CloudWatch real (`/kiro/microservices/backend`)
  - Variables sensibles en `.env` (nunca en código)

- [ ] **Task 8: Seed Knowledge Base** — `scripts/seed_knowledge_base.py`
  - Insertar errores conocidos en DynamoDB con `confidence=0.9`
  - Tipos: DatabaseTimeoutError, BiometricServiceFailure, InventoryLockError
  - Requiere `terraform apply` previo para crear las tablas
