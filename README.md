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

**El Agente SRE Autónomo**  combina **Inteligencia Artificial (AWS Bedrock)** y **Site Reliability Engineering (SRE)** para analizar logs estructurados, correlacionar fallos en arquitecturas complejas y localizar cuellos de botella en segundos. 

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

## 🤝 Flujo de Trabajo (De la Idea a Producción)

El desarrollo del proyecto integra herramientas avanzadas: **MCP, Skills, Hooks, Powers, AWS y Git + PRs**. El ciclo de vida sigue este flujo:

```text
Setup ➔ Spec ➔ Build ➔ Review ➔ Deploy
```

### 🛠️ Construir en Equipo + PRs
1. Cada desarrollador implementa su spec en su rama (ej: `feat/filter-done`).
2. Kiro trabaja en modo *Supervised*; los **Hooks** corren los tests automáticamente al guardar.
3. Commit con mensaje generado por IA, push y apertura de Pull Request (PR).
4. Descripción del PR con link al spec y guía de cómo probarlo.

### 🚀 Review, Merge y Deploy a AWS
1. Review de cada PR utilizando `/pr-review` + checklist de verificación.
2. Feedback → prompt acotado → nuevo diff → aprobación humana.
3. Merge a la rama `main` y deploy automático a **AWS**.
4. **CloudWatch** observa y monitorea en producción.

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

## 🚀 Quick Start en 5 Minutos (Despliegue AWS)

Al ser el repositorio del Agente y despliegue, la configuración se centra en levantar la infraestructura:

```bash
git clone https://github.com/DevMasters-Aws-Team/kiro-sre-Monitor-Agent.git
cd kiro-sre-Monitor-Agent/infrastructure
terraform init
terraform apply -auto-approve
```

---

## 🛠️ Stack Tecnológico Global

| Capa | Tecnología |
|------------|-----------|
| **Frontend** | React + Vite |
| **Backend API** | Node/Python (Microservicios) |
| **Agente / IA** | Python, AWS Bedrock (Claude 3), MCP, Powers, Skills |
| **DevOps / Infra** | AWS (CloudWatch, ECS, Lambda), Terraform, Docker, Git Hooks |

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
