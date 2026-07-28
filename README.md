# Carmen — Kiro SRE Monitor Agent

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge)
![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock_Nova_Lite-FF9900?style=for-the-badge&logo=amazon-aws)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=for-the-badge)
![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?style=for-the-badge&logo=terraform)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)

**Agente SRE Autónomo de Observabilidad, Diagnóstico y Auto-remediación con IA**

*Proyecto Integrador — Hackathon Kiro DevMasters AWS 2026*

</div>

---

## 🎯 ¿Qué es Carmen?

**Carmen** es un agente SRE (Site Reliability Engineering) autónomo que combina **Amazon Bedrock**, **LangChain** y **AWS CloudWatch** para detectar, diagnosticar y remediar incidentes en microservicios de forma automática.

Cuando un microservicio del Backend emite un error, Carmen se activa en milisegundos, analiza la causa raíz con IA, y — si la confianza y el riesgo lo permiten — ejecuta la skill de remediación sin intervención humana.

### El flujo en 3 pasos

```
OBSERVE            REASON             ACT
   │                  │                │
Recibe alerta  → Bedrock analiza → Ejecuta skill
de CloudWatch    causa raíz con     (restart, scale,
vía webhook      context real       clear_cache...)
```

---

## 🏆 Criterios del Hackathon — Estado de Implementación

| Criterio | Implementación | Estado |
|----------|---------------|--------|
| **MCP** | `aws-docs` (uvx), `kiro-cloudwatch`, `kiro-dynamodb` en `.kiro/settings/mcp.json` | ✅ |
| **Skills** | `restart_service`, `scale_up`, `clear_cache`, `purge_queue` — LangChain `@tool` | ✅ |
| **Hooks** | 4 hooks en `.kiro/hooks/`: lint, tests, skill-guard, webhook-log | ✅ |
| **Powers (IAM)** | Terraform con roles Least Privilege — documentado en steering | ✅ |
| **AWS** | EC2 (agente) + CloudWatch (logs) + Bedrock (IA) + DynamoDB + Terraform | ✅ |
| **Git + PRs** | Organización `DevMasters-Aws-Team` · branches · PRs | ✅ |
| **Spec (Kiro SDD)** | `.kiro/specs/sre-agent/` con requirements, design, tasks | ✅ |
| **Steering** | 6 archivos en `.kiro/steering/` con reglas del agente | ✅ |

---

## 🏗️ Arquitectura del Sistema

```
┌──────────────────────────────────────────────────────────────────┐
│                   ECOSISTEMA KIRO SRE                            │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │  Frontend   │    │   Backend   │    │    Agente Carmen     │ │
│  │  (Amplify)  │◀───│   (EC2)     │───▶│      (EC2)          │ │
│  │  React+Vite │    │  FastAPI    │    │  FastAPI+Bedrock     │ │
│  │  :3000      │    │  :8000      │    │  :8001               │ │
│  └─────────────┘    └──────┬──────┘    └────────┬────────────┘ │
│                             │                    │               │
│                             ▼                    ▼               │
│                     ┌──────────────┐    ┌───────────────────┐  │
│                     │  CloudWatch  │    │   Amazon Bedrock   │  │
│                     │  Log Group   │    │   Nova Lite        │  │
│                     │  /kiro/...   │    │   (LLM reasoning)  │  │
│                     └──────────────┘    └───────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    AWS Infrastructure                      │  │
│  │  DynamoDB · EventBridge · Lambda · IAM · Cognito · SNS    │  │
│  │              (Terraform — Least Privilege)                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔌 MCP — Model Context Protocol

Tres conectores MCP configurados en `.kiro/settings/mcp.json`:

| Servidor MCP | Tipo | Herramientas | Propósito |
|-------------|------|-------------|-----------|
| `aws-docs` | uvx (oficial Amazon) | `search_documentation`, `read_documentation` | Consultar docs AWS mientras se desarrolla |
| `kiro-cloudwatch` | Python custom | `get_recent_errors`, `get_service_health`, `get_incident_summary` | Consultar CloudWatch desde Kiro IDE |
| `kiro-dynamodb` | Python custom | `query_knowledge_base`, `list_known_errors` | Consultar Knowledge Base desde Kiro IDE |

Los MCP servers Python se encuentran en `src/mcp/` y usan el protocolo JSON-RPC 2.0 via stdio.

---

## ⚙️ Skills de Remediación

Implementadas como LangChain `@tool` decorators — el LLM (Bedrock) las invoca directamente:

| Skill | Trigger | AWS Service | Risk | Auto-exec |
|-------|---------|-------------|------|-----------|
| `restart_service` | HTTP 500 persistente, DatabaseTimeoutError | ECS | medium | ✅ |
| `scale_up` | CPU > 80%, latencia alta, error rate > 5% | ECS | medium | ❌ requiere confirm |
| `clear_cache` | BiometricServiceFailure, datos stale | ElastiCache | low | ✅ |
| `purge_queue` | InventoryLockError, DLQ creciente | SQS | high | ❌ requiere confirm |

Catálogo completo en: `GET http://localhost:8001/skills`

---

## 🪝 Hooks de Kiro IDE

Configurados en `.kiro/hooks/`:

| Hook | Trigger | Acción |
|------|---------|--------|
| `lint-on-save` | `fileEdited *.py` | `ruff check src/ --fix` |
| `run-tests-on-save` | `fileEdited src/**/*.py` | `pytest tests/ -v` |
| `skill-safety-guard` | `preToolUse shell` | Bloquea skills de alto riesgo en prod |
| `webhook-process-log` | `postToolUse web` | Log estructurado de incidentes |

---

## 🚀 Quick Start

### Prerrequisitos
- Python 3.12+
- `pip install poetry` o equivalente

### 1. Instalar dependencias

```bash
git clone https://github.com/DevMasters-Aws-Team/kiro-sre-Monitor-Agent.git
cd kiro-sre-Monitor-Agent
pip install .
```

### 2. Configurar entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales AWS
```

Variables clave:

| Variable | Descripción | Default |
|----------|-------------|---------|
| `KIRO_USE_MOCK_AWS` | `true` = mock local, `false` = AWS real | `true` |
| `KIRO_BEDROCK_MODEL_ID` | Modelo Bedrock a usar | `us.amazon.nova-lite-v1:0` |
| `KIRO_AWS_ACCESS_KEY_ID` | Access key AWS | — |
| `KIRO_AWS_SECRET_ACCESS_KEY` | Secret key AWS | — |
| `KIRO_LOG_GROUP_NAME` | Log group CloudWatch del Backend | `/kiro/microservices/backend` |
| `KIRO_ENABLE_AUDIT_TRAIL` | Guardar acciones en DynamoDB | `false` |

### 3. Levantar el agente

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

### 4. Verificar funcionamiento

```bash
# Health check
curl http://localhost:8001/health

# Verificar Bedrock
curl -X POST http://localhost:8001/chat/test

# Simular incidente
curl -X POST "http://localhost:8001/webhook/chaos?service=sales-service&error_type=DatabaseTimeoutError"

# Ver catálogo de skills
curl http://localhost:8001/skills

# Chat con Carmen
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿cuál es el estado del sistema?"}'
```

---

## 📡 API Reference

### Base URL: `http://localhost:8001`

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Estado del agente |
| POST | `/webhook` | Recibe alertas CloudWatch del Backend |
| POST | `/webhook/test` | Simula alerta con datos predefinidos |
| POST | `/webhook/chaos?service=X&error_type=Y` | Simula fallo controlado |
| POST | `/chat` | Chat conversacional con Carmen (Bedrock) |
| POST | `/chat/test` | Verifica conectividad con Bedrock |
| GET | `/incidents` | Últimos N incidentes analizados |
| GET | `/skills` | Catálogo completo de skills |
| POST | `/skills/{name}` | Invocar skill directamente |
| GET | `/docs` | Swagger UI interactivo |

### Modelos Bedrock soportados

| Model ID | Familia | Costo aprox. |
|----------|---------|-------------|
| `us.amazon.nova-lite-v1:0` | Amazon Nova | ~$0.0001/1K tokens |
| `us.amazon.nova-pro-v1:0` | Amazon Nova | ~$0.0008/1K tokens |
| `anthropic.claude-3-haiku-20240307-v1:0` | Claude | ~$0.00025/1K tokens |
| `anthropic.claude-3-5-sonnet-20241022-v2:0` | Claude | ~$0.003/1K tokens |

---

## 🧠 Motor de Decisión

```
Alerta recibida
      │
      ├─ ¿Bedrock disponible? ──▶ SÍ ──▶ Diagnóstico con LLM
      │                                   (confidence + action)
      └─ NO ──▶ Decision Engine (reglas)
                (DatabaseTimeoutError → restart_service, etc.)
                      │
                      ▼
              confidence ≥ 0.8 AND risk = low/medium
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
    Auto-ejecutar             Pedir confirmación
    skill vía @tool           o escalar a humano
          │
          ▼
    AuditTable DynamoDB
```

---

## 🗂️ Estructura del Proyecto

```
kiro-sre-Monitor-Agent/
├── .kiro/
│   ├── settings/
│   │   └── mcp.json              ← 3 servidores MCP configurados
│   ├── hooks/
│   │   ├── lint-on-save.json
│   │   ├── run-tests-on-save.json
│   │   ├── skill-safety-guard.json
│   │   └── webhook-process-log.json
│   ├── steering/
│   │   ├── global_steering.md    ← Reglas cognitivas del agente
│   │   ├── agent_prompts.md      ← System prompts
│   │   ├── integrations.md       ← Conexiones AWS
│   │   ├── architecture_specs.md ← Arquitectura
│   │   ├── terraform.md          ← IaC
│   │   └── testing.md            ← Estrategia de tests
│   └── specs/
│       └── sre-agent/
│           ├── requirements.md   ← 5 requisitos + correctness properties
│           ├── design.md         ← Arquitectura detallada
│           └── tasks.md          ← 8 tasks con estado
├── src/
│   ├── main.py                   ← FastAPI entry point
│   ├── config.py                 ← Settings (pydantic-settings)
│   ├── agents/
│   │   ├── orchestrator.py       ← Observe→Reason→Act + incident history
│   │   ├── decision_engine.py    ← Motor de reglas (fallback LLM)
│   │   ├── event_handler.py      ← Handler EventBridge
│   │   ├── llm_provider.py       ← LangChain + Bedrock client
│   │   └── sre_autonomo/
│   │       ├── agent.py          ← Entry point del agente
│   │       └── prompts.py        ← System prompt + análisis de trazas
│   ├── infrastructure/
│   │   └── clients.py            ← AWS clients (real + mock completo)
│   ├── mcp/
│   │   ├── cloudwatch_mcp_server.py ← MCP server CloudWatch (JSON-RPC 2.0)
│   │   └── dynamodb_mcp_server.py   ← MCP server DynamoDB (JSON-RPC 2.0)
│   ├── models/
│   │   └── alerts.py             ← CloudWatchAlert + WebhookResponse
│   ├── routers/
│   │   ├── webhook.py            ← /webhook /webhook/test /webhook/chaos
│   │   ├── chat.py               ← /chat /chat/test /incidents
│   │   ├── skills.py             ← /skills GET+POST catálogo
│   │   ├── health.py             ← /health
│   │   └── registry.py           ← Registro de routers
│   └── skills/
│       ├── restart_service.py    ← @tool ECS forceNewDeployment
│       ├── scale_up.py           ← @tool ECS update desiredCount
│       ├── clear_cache.py        ← @tool ElastiCache/Redis
│       └── purge_queue.py        ← @tool SQS purge
├── terraform/                    ← IaC completo (9 módulos)
├── tests/                        ← 8 archivos de tests
├── Dockerfile                    ← Multi-stage build
├── docker-compose.yml
├── Makefile
├── pyproject.toml                ← Dependencias (hatchling)
└── .env.example
```

---

## 🧪 Tests

```bash
# Todos los tests
python -m pytest tests/ -v

# Con cobertura
python -m pytest tests/ --cov=src --cov-report=term-missing

# Test específico
python -m pytest tests/test_decision_engine.py -v
```

---

## 🐳 Docker

```bash
docker build -t kiro-agent:latest .
docker run -p 8001:8001 --env-file .env kiro-agent:latest
```

---

## 🌐 Demo — Flujo Completo

Para reproducir el demo completo del hackathon en local:

```bash
# Terminal 1 — Backend (genera logs a CloudWatch)
cd Backend && uvicorn src.main:app --port 8000 --reload

# Terminal 2 — Agente Carmen (diagnostica y remedia)
cd kiro-sre-Monitor-Agent && uvicorn src.main:app --port 8001 --reload

# Terminal 3 — Frontend (dashboard en tiempo real)
cd Frontend && npm run dev

# Terminal 4 — Inyectar fallo y ver a Carmen en acción
curl -X POST http://localhost:8000/chaos/timeout
# Carmen recibe el webhook → Bedrock diagnostica → skill ejecutada
# Ver en http://localhost:3000 el dashboard y el chat
```

---

## 👥 Equipo DevMasters AWS Team

<table>
<tr>
<td align="center"><sub><b>Ashley Zifrikc Villanueva</b></sub></td>
<td align="center"><sub><b>Julio Vargas</b></sub></td>
<td align="center"><sub><b>Jennifer Nicole Solis</b></sub></td>
<td align="center"><sub><b>Juan Aulla Solis</b></sub></td>
<td align="center"><sub><b>Jesus</b></sub></td>
</tr>
</table>

<div align="center">

**Desarrollado con ❤️ para el Hackathon Kiro DevMasters AWS 2026**

[![Agent](https://img.shields.io/badge/🔗_Agent-Repo-blue?style=for-the-badge)](https://github.com/DevMasters-Aws-Team/kiro-sre-Monitor-Agent/)
[![Backend](https://img.shields.io/badge/🔗_Backend-Repo-green?style=for-the-badge)](https://github.com/DevMasters-Aws-Team/Backend)
[![Frontend](https://img.shields.io/badge/🔗_Frontend-Repo-61DAFB?style=for-the-badge)](https://github.com/DevMasters-Aws-Team/Frontend)

</div>
