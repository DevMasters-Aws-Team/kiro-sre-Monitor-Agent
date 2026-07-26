# Kiro Monitor Agente SRE Autónomo para Microservicios


<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![AWS](https://img.shields.io/badge/AWS-Cloud-orange?style=flat-square&logo=amazon-aws)
![Python](https://img.shields.io/badge/Python-FastAPI-blue?style=flat-square&logo=python)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=flat-square&logo=react)
![Vite](https://img.shields.io/badge/Vite-Build%20Tool-646CFF?style=flat-square&logo=vite)
![Terraform](https://img.shields.io/badge/Terraform-IaC-purple?style=flat-square&logo=terraform)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)
![License](https://img.shields.io/badge/license-MIT-yellow)

**Plataforma Integral de Observabilidad, Diagnóstico y Auto-remediación con IA**

</div>

---

## 🎯 Descripción General

**El Agente SRE Autónomo** combina **Inteligencia Artificial (AWS Bedrock)** y **Site Reliability Engineering (SRE)** para analizar logs estructurados, correlacionar fallos en arquitecturas complejas y localizar cuellos de botella en segundos. 

El proyecto integra todas las piezas clave para un desarrollo y despliegue modernos: **MCP, Skills, Hooks, Powers, AWS y Git + PRs**. 

### 💼 Sectores de Aplicación
Esta solución es crítica para empresas de alta transaccionalidad, como:

<table>
<tr>
<td align="center">💳<br><b>Fintech y Banca</b></td>
<td align="center">🛒<br><b>E-commerce</b></td>
<td align="center">🌐<br><b>SaaS Empresarial</b></td>
<td align="center">📱<br><b>Telecomunicaciones</b></td>
<td align="center">🎬<br><b>Streaming</b></td>
</tr>
</table>

### 🎓 Contexto del Proyecto

Desarrollado para resolver retos de observabilidad, diseñado para equipos con conocimientos en:
- ✅ **SRE & Backend** con Python (FastAPI, integraciones con AWS Bedrock, Lambdas)
- ✅ **Cloud & DevOps** con Terraform (IaC) y Docker/ECS
- ✅ **Frontend** con React y Vite (Dashboard de salud y telemetría)

---

## 😰 Problema que Resolvemos

En arquitecturas modernas, una simple transacción atraviesa decenas de microservicios. Cuando ocurre una excepción (ej. timeout de BD), el impacto se propaga en cascada. Actualmente, la respuesta es manual: un ingeniero debe conectarse por SSH, rastrear el ID de transacción entre cientos de logs, revisar grupos de seguridad y código fuente, elevando drásticamente el MTTR (*Mean Time To Recovery*).

### 💸 Desafíos de Negocio

```
┌──────────────────────────────────────────────────────────────┐
│  Cada minuto de inactividad (Downtime) representa:           │
│                                                              │
│  💰 Pérdida directa de ingresos transaccionales              │
│  😔 Daño a la reputación de la marca y frustración del user  │
│  📉 Fatiga operativa en los ingenieros de guardia (On-call)  │
│  🔄 Cuellos de botella que paralizan colas enteras           │
│                                                              │
│  "El tiempo de resolución manual escala los costos"          │
└──────────────────────────────────────────────────────────────┘
```

## ✨ Nuestra Solución

**Kiro Agent** es una solución impulsada por IA que actúa como un ingeniero SRE virtual. Ingesta logs estructurados (JSON) en tiempo real a través de AWS CloudWatch, utiliza el razonamiento lógico de Claude 3 (vía AWS Bedrock) para identificar la causa raíz, y, de ser una tarea segura, invoca Skills (Lambdas) para auto-remediar el problema. Todo esto se monitorea desde una UI desarrollada en React.

---

## 🔎 Inteligencia y Contexto (Model Context Protocol - MCP)

Para optimizar cómo Bedrock interactúa con nuestro entorno sin "alucinar", implementamos conectores **MCP (Model Context Protocol)** estratégicos:

- **MCP AWS Log Explorer:** Proporciona a Bedrock herramientas exclusivas para consultar CloudWatch Logs Insights, filtrando el ruido antes del análisis semántico.
- **MCP Terraform State Reader:** Permite al agente leer el estado de la infraestructura (IaC) para comprender las dependencias reales.
- **MCP GitHub Repo Context:** Permite leer el código fuente del microservicio fallido, contrastando el error del log con el manejador de errores real.

---

##  🏗️ Arquitectura del Sistema

### Diagrama de Alto Nivel

**☁️ Recursos AWS Utilizados:**
- ✅ **AWS Bedrock**: Motor cognitivo del agente (Claude 3).
- ✅ **CloudWatch Logs & Metrics**: Ingesta de logs estructurados JSON.
- ✅ **Amazon EventBridge**: Bus de captura de anomalías para disparar Kiro.
- ✅ **AWS Lambda**: Funciones serverless ejecutadas como "Skills".
- ✅ **AWS IAM**: Roles restrictivos de seguridad.
- ✅ **AWS ECS con Fargate**: Despliegue de contenedores.

### 🔄 Flujo de Remediación

```text
Microservicio → Emite Log JSON de Error
              ↓
Amazon CloudWatch → Amazon EventBridge (Detecta anomalía)
              ↓
Agente Kiro (Python) → Despierta tras el evento
              ↓
Kiro usa Bedrock + MCP (Logs, TF State, GitHub) para razonar
              ↓
Kiro toma Decisión → Invoca AWS Lambda (Skill de Remediación)
              ↓
Frontend (React UI) y Slack/Telegram (Notificación)
```

---

## 📦 Repositorios del Proyecto (Organización Multi-Repo)

El ecosistema del proyecto se divide en 3 repositorios alojados en la organización [DevMasters-Aws-Team](https://github.com/DevMasters-Aws-Team). 

**Este repositorio actual es el Principal (`kiro-sre-Monitor-Agent`)**, encargado del Agente SRE, despliegues y configuración global.

### 🏗️ Estructura
```
DevMasters-Aws-Team
│
├─── 🌍 kiro-sre-Monitor-Agent (este repo)
│    └── Agente Kiro (Bedrock, MCP, Orquestación) e Infraestructura de despliegue (Terraform)
│
├─── ⚙️ Backend
│    └── API REST de los microservicios simulados/reales que el Agente va a monitorear
│
└─── 📊 Frontend
     └── UI/UX Dashboard de observabilidad en React + Vite
```

> **💡 Nota sobre la arquitectura Backend/Agente:** 
> El Agente SRE (Kiro) se aloja y corre en este repositorio principal (`kiro-sre-Monitor-Agent`) como un servicio de monitorización independiente. El repositorio `Backend` separado sirve para alojar la lógica de negocio (las APIs y microservicios) que Kiro se encargará de vigilar y arreglar cuando fallen.

### 1️⃣ 🌍 [Kiro SRE Monitor Agent](https://github.com/DevMasters-Aws-Team/kiro-sre-Monitor-Agent/) (Este Repositorio)
**Propósito:** Contiene el bucle principal del agente, conectores MCP, "Powers" de IA, orquestación, y configuración de infraestructura en AWS (Terraform).

### 2️⃣ ⚙️ [Backend API](https://github.com/DevMasters-Aws-Team/Backend)
**Propósito:** APIs, lógica de negocio y endpoints que generan los logs monitoreados por el Agente.

### 3️⃣ 📊 [Frontend UI](https://github.com/DevMasters-Aws-Team/Frontend)
**Propósito:** Dashboard interactivo para observabilidad.

---

## 🚀 Quick Start (Local Development)

### Prerequisitos

- Python 3.12 o superior
- Poetry
- Docker (opcional)

### 1. Instalar dependencias

```bash
git clone https://github.com/DevMasters-Aws-Team/kiro-sre-Monitor-Agent.git
cd kiro-sre-Monitor-Agent

python -m pip install poetry
python -m poetry install
```

### 2. Configurar variables de entorno

```bash
copy .env.example .env
```

Editar `.env`:

```env
# Modo mock (sin AWS real)
KIRO_USE_MOCK_AWS=true

# Para produccion con AWS real
# KIRO_USE_MOCK_AWS=false
# AWS_REGION=us-east-1
# BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

### 3. Levantar el agent

```bash
python -m poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

### 4. Verificar que funciona

```bash
# Test basico
curl -X POST http://localhost:8001/webhook/test

# Test con chaos
curl -X POST http://localhost:8001/webhook/chaos?service=payment-service
```

---

## 📡 Endpoints del Agent

### Base URL: `http://localhost:8001`

| Ruta | Metodo | Descripcion |
|------|--------|-------------|
| `/webhook` | POST | Recibe alertas de CloudWatch/EventBridge y del Backend |
| `/webhook/test` | POST | Test de diagnostico con datos simulados |
| `/webhook/chaos` | POST | Simula fallo en un servicio especifico |
| `/chat` | POST | Chat conversacional con Carmen (usa Bedrock) |
| `/chat/test` | POST | Verifica si Bedrock esta conectado |

### Verificar conexion con Bedrock

```bash
curl -X POST http://localhost:8001/chat/test
```

**Respuesta esperada:**
```json
{
  "status": "ok",
  "llm_available": true,
  "model": "us.amazon.nova-lite-v1:0"
}
```

Si `llm_available` es `false`, revisar que `KIRO_USE_MOCK_AWS=false` en el `.env`.

### Chat con Carmen

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"hola\"}"
```

**Respuesta esperada:** `"source": "llm"` (si dice `"fallback"`, Bedrock no respondio -- revisar credenciales y model ID en `.env`).

### Modelos Bedrock soportados

El agente detecta automaticamente el formato de request segun el modelo:

| Model ID | Familia | Costo |
|----------|---------|-------|
| `us.amazon.nova-lite-v1:0` | Amazon Nova | Gratis en free tier |
| `us.amazon.nova-pro-v1:0` | Amazon Nova | Bajo |
| `anthropic.claude-3-haiku-20240307-v1:0` | Anthropic Claude | Bajo |
| `anthropic.claude-3-5-sonnet-20241022-v2:0` | Anthropic Claude | Medio |

### Ejemplo: Test de diagnostico

```bash
curl -X POST http://localhost:8001/webhook/test
```

**Respuesta:**
```json
{
  "status": "analyzed",
  "alert_id": "ede9b5e1-fcab-49ae-a798-143a6a81d416",
  "analysis": "## Diagnóstico del Agente SRE\n\n**Severidad**: CRITICA\n**Causa raíz**: CPU utilization exceeded 80% threshold\n...",
  "actions_suggested": []
}
```

### Ejemplo: Simular fallo

```bash
curl -X POST "http://localhost:8001/webhook/chaos?service=inventory-service"
```

---

## 🧠 Flujo de Decision del Agent

```text
┌─────────────────────────────────────────────────────────────────┐
│  FLUJO OBSERVE → REASON → ACT                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. OBSERVE (Observar)                                          │
│     ├── Recibe alerta de CloudWatch/EventBridge                 │
│     ├── Obtiene logs recientes del servicio afectado            │
│     └── Recopila metricas y contexto                            │
│                                                                  │
│  2. REASON (Razonar)                                            │
│     ├── Analiza logs con Bedrock (Claude 3)                     │
│     ├── Clasifica severidad (CRITICA, ALTA, MEDIA, BAJA)        │
│     ├── Calcula confianza del diagnostico                       │
│     └── Determina accion recomendada                            │
│                                                                  │
│  3. ACT (Actuar)                                                │
│     ├── Si confianza > 80% y accion segura: ejecuta automatico  │
│     ├── Si confianza < 80%: sugiere accion para humano          │
│     ├── Registra en audit trail (DynamoDB)                      │
│     └── Notifica al Frontend                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Skills Disponibles

| Skill | Descripcion | Servicio AWS |
|-------|-------------|--------------|
| `restart_service` | Reinicia un servicio en ECS | ECS |
| `scale_up` | Escala instancias de un servicio | ECS/Auto Scaling |
| `clear_cache` | Limpia cache de Redis/ElastiCache | ElastiCache |
| `purge_queue` | Limpia cola SQS con mensajes stuck | SQS |

---

## 🏗️ Estructura del Repositorio

```text
kiro-sre-Monitor-Agent/
├── 📂 .kiro/steering/                # Fase de Setup / SDD
│   ├── global_steering.md            # Reglas cognitivas del agente
│   ├── agent_prompts.md              # System prompts maestros
│   ├── integrations.md               # Conexiones AWS
│   └── architecture_specs.md         # Arquitectura Event-Driven
│
├── 📂 terraform/                     # Infraestructura como Código
│   ├── main.tf                       # Provider + backend S3
│   ├── variables.tf                  # Variables del proyecto
│   ├── eventbridge.tf                # Event Bus + Rules
│   ├── cloudwatch.tf                 # Log Groups + Alarms
│   ├── lambda.tf                     # Skills functions
│   ├── iam.tf                        # Roles + Policies
│   ├── dynamodb.tf                   # Tablas de datos
│   └── cognito.tf                    # User Pool
│
├── 📂 src/                           # Código del Orquestador
│   ├── main.py                       # Entry point FastAPI
│   ├── config.py                     # Configuracion (pydantic-settings)
│   ├── agents/
│   │   ├── orchestrator.py           # Bucle Observe → Reason → Act
│   │   ├── decision_engine.py        # Motor de decisiones
│   │   └── event_handler.py          # Handler de eventos
│   ├── infrastructure/
│   │   └── clients.py                # Clientes AWS (mock/real)
│   ├── skills/
│   │   ├── restart_service.py        # Skill de reinicio
│   │   ├── scale_up.py               # Skill de escalado
│   │   ├── clear_cache.py            # Skill de limpieza cache
│   │   └── purge_queue.py            # Skill de limpieza cola
│   ├── models/
│   │   └── alerts.py                 # Modelos de datos
│   └── routers/
│       └── webhook.py                # Endpoints webhook
│
├── 📂 tests/                         # Tests unitarios
├── Dockerfile                        # Container para deploy
├── docker-compose.yml                # Docker Compose
├── Makefile                          # Comandos automatizados
├── pyproject.toml                    # Dependencias (Poetry)
└── .env.example                      # Template de variables
```

---

## 🛠️ Stack Tecnológico Global

| Capa | Tecnología |
|------------|-----------|
| **Frontend** | React 18 + Vite 5 + TypeScript + TailwindCSS |
| **Backend API** | Python 3.12 + FastAPI + Poetry + Docker |
| **Agente / IA** | Python 3.12, AWS Bedrock (Claude 3 Sonnet), MCP, Powers, Skills |
| **DevOps / Infra** | Terraform, AWS (CloudWatch, ECS Fargate, Lambda, EventBridge, DynamoDB, Cognito), Docker |
| **Observabilidad** | CloudWatch Logs (JSON estructurado) + Alarmas + Metric Filters |

---

## 🧪 Tests

```bash
# Correr todos los tests
python -m poetry run pytest

# Con cobertura
python -m poetry run pytest --cov=src --cov-report=html

# Tests especificos
python -m poetry run pytest tests/test_decision_engine.py -v
```

---

## 🐳 Docker

```bash
# Construir imagen
docker build -t kiro-agent:latest .

# Ejecutar
docker run -p 8001:8001 --env-file .env kiro-agent:latest

# O con Docker Compose (junto con Backend)
docker-compose up -d
```

---

## 📜 Contrato de Integración (Eventos)

### Request (Payload de EventBridge)

```json
{
  "incidentId": "INC-0823",
  "timestamp": "2024-11-20T14:32:00Z",
  "serviceName": "payment-gateway-svc",
  "logLevel": "ERROR",
  "message": "Connection timeout acquiring connection from pool"
}
```

### Response (Decisión del Agente)
```json
{
  "status": "REMEDIATED",
  "actionsTaken": [
    {
      "skill": "AWS_ECS_RESTART_TASK",
      "target": "payment-gateway-svc"
    }
  ]
}
```

---

## 🔄 Integracion con Backend y Frontend

```text
┌─────────────────────────────────────────────────────────────────┐
│  FLUJO DE INTEGRACION                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Backend (localhost:8000)                                        │
│  └── Genera logs de microservicios                              │
│      └── Envia a CloudWatch (o genera en memoria)               │
│                                                                  │
│  Agent (localhost:8001)                                          │
│  └── Recibe alertas via webhook                                 │
│      └── Analiza con Bedrock                                    │
│      └── Ejecuta skills de remediacion                          │
│      └── Retorna diagnostico                                    │
│                                                                  │
│  Frontend (localhost:3000)                                       │
│  └── Muestra dashboard en tiempo real                           │
│      └── Consulta Backend: /api/services, /api/logs             │
│      └── Consulta Agent: /webhook/*                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 👥 Equipo (DevMasters AWS Team)

<table>
<tr>
<td align="center" width="150">
<sub><b>Ashley Zifrikc Villanueva</b></sub><br />
<a href="#"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" /></a>
<a href="#"><img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" /></a>
</td>
<td align="center" width="150">
<sub><b>Julio Vargas</b></sub><br />
<a href="#"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" /></a>
<a href="#"><img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" /></a>
</td>
<td align="center" width="150">
<sub><b>Jennifer Nicole Solis</b></sub><br />
<a href="#"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" /></a>
<a href="#"><img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" /></a>
</td>
<td align="center" width="150">
<sub><b>Juan Aulla Solis</b></sub><br />
<a href="#"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" /></a>
<a href="#"><img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" /></a>
</td>
<td align="center" width="150">
<sub><b>Jesus</b></sub><br />
<a href="#"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" /></a>
<a href="#"><img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" /></a>
</td>
</tr>
</table>

---

<div align="center">

### 🌟 Si este proyecto te fue útil, ¡dale una estrella! ⭐

**Desarrollado con ❤️ por DevMasters AWS Team**

[![Agent](https://img.shields.io/badge/🔗%20Agent-Repo-blue?style=for-the-badge)](https://github.com/DevMasters-Aws-Team/kiro-sre-Monitor-Agent/)
[![Backend](https://img.shields.io/badge/🔗%20Backend-Repo-green?style=for-the-badge)](https://github.com/DevMasters-Aws-Team/Backend)
[![Frontend](https://img.shields.io/badge/🔗%20Frontend-Repo-61DAFB?style=for-the-badge)](https://github.com/DevMasters-Aws-Team/Frontend)

</div>
