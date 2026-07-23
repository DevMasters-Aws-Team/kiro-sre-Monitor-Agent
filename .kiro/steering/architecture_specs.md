# Architecture Specs - Kiro SRE Agent (Orquestador)

## Arquitectura Event-Driven

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AWS CLOUD                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              OBSERVABILITY LAYER                                │ │
│  │                                                                │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │ │
│  │  │user-svc  │  │order-svc │  │pay-svc   │  │auth-svc  │     │ │
│  │  │(ECS Task)│  │(ECS Task)│  │(ECS Task)│  │(ECS Task)│     │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │ │
│  │       │              │              │              │            │ │
│  │       └──────────────┼──────────────┼──────────────┘            │ │
│  │                      ▼                                         │ │
│  │              ┌──────────────────┐                              │ │
│  │              │   CloudWatch     │                              │ │
│  │              │   Logs + Alarms  │                              │ │
│  │              └────────┬─────────┘                              │ │
│  └───────────────────────┼────────────────────────────────────────┘ │
│                          │                                          │
│  ┌───────────────────────┼────────────────────────────────────────┐ │
│  │              EVENT ROUTING LAYER                                │ │
│  │                       ▼                                        │ │
│  │              ┌──────────────────┐                              │ │
│  │              │   EventBridge    │                              │ │
│  │              │   Event Bus      │                              │ │
│  │              └────────┬─────────┘                              │ │
│  └───────────────────────┼────────────────────────────────────────┘ │
│                          │                                          │
│  ┌───────────────────────┼────────────────────────────────────────┐ │
│  │              INTELLIGENCE LAYER                                 │ │
│  │                       ▼                                        │ │
│  │              ┌──────────────────┐                              │ │
│  │              │  Lambda:         │                              │ │
│  │              │  kiro-orchestrator│                              │ │
│  │              └────────┬─────────┘                              │ │
│  │                       │                                        │ │
│  │          ┌────────────┼────────────┐                           │ │
│  │          ▼            ▼            ▼                           │ │
│  │  ┌─────────────┐ ┌────────┐ ┌─────────────┐                  │ │
│  │  │   Bedrock   │ │DynamoDB│ │ CloudWatch  │                  │ │
│  │  │   (LLM)     │ │(KB)    │ │ (Context)   │                  │ │
│  │  └─────────────┘ └────────┘ └─────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                          │
│  ┌───────────────────────┼────────────────────────────────────────┐ │
│  │              REMEDIATION LAYER                                  │ │
│  │                       ▼                                        │ │
│  │  ┌─────────────┐ ┌────────────┐ ┌─────────────┐              │ │
│  │  │ Lambda:     │ │ Lambda:    │ │ Lambda:     │              │ │
│  │  │ restart-svc │ │ scale-up   │ │ purge-queue │              │ │
│  │  └─────────────┘ └────────────┘ └─────────────┘              │ │
│  │                       │                                        │ │
│  │                       ▼                                        │ │
│  │              ┌──────────────────┐                              │ │
│  │              │   SNS / SES      │                              │ │
│  │              │   (Notifications)│                              │ │
│  │              └──────────────────┘                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Infraestructura Terraform

### Módulos

#### main.tf
```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket = "kiro-terraform-state"
    key    = "kiro-agent/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}
```

#### variables.tf
```hcl
variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  default = "kiro-monitor"
}

variable "bedrock_model_id" {
  default = "anthropic.claude-3-sonnet-20240229-v1:0"
}
```

### Recursos Principales

#### EventBridge
- Event Bus: `kiro-monitor-events`
- Rules: alarm-trigger, ecs-failure, app-error
- Targets: Lambda orchestrator

#### CloudWatch
- Log Groups: uno por microservicio (`/ecs/kiro-*`)
- Alarms: error-rate, latency, service-down
- Metric Filters: error-count desde logs JSON
- Dashboards: métricas en tiempo real

#### Lambda
- `kiro-orchestrator`: Función principal (512MB, 60s timeout)
- `kiro-restart-service`: Skill de restart (256MB, 30s)
- `kiro-scale-up`: Skill de escalado (256MB, 30s)
- `kiro-purge-queue`: Skill de purga SQS (128MB, 15s)
- `kiro-send-alert`: Skill de notificación (128MB, 10s)

#### DynamoDB
- `KnowledgeTable`: Base de conocimiento de errores
- `TicketsTable`: Tickets de incidencia
- `IncidentsTable`: Historial de incidentes
- `AuditTable`: Audit trail de acciones del agente

#### IAM
- `KiroMonitorAgentRole`: Rol principal (lectura)
- `KiroRemediationRole`: Rol de skills (escritura limitada)
- `KiroPermissionsBoundary`: Boundary policy (denegaciones)

#### Cognito
- User Pool: `kiro-dashboard-users`
- App Client: `kiro-dashboard-web`
- Domain: `kiro-auth`

### Outputs
```hcl
output "orchestrator_lambda_arn" {
  value = aws_lambda_function.orchestrator.arn
}

output "event_bus_arn" {
  value = aws_cloudwatch_event_bus.kiro.arn
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.dashboard.id
}

output "api_endpoint" {
  value = aws_lb.backend.dns_name
}
```

## Secuencia de Despliegue

```
1. terraform init
2. terraform plan -var="environment=dev"
3. terraform apply
4. Deploy Backend (Docker → ECS)
5. Deploy Frontend (GitHub → Amplify)
6. Configurar alarmas de CloudWatch
7. Crear entradas iniciales en KnowledgeTable
8. Verificar flujo completo con /chaos endpoint
```

## Costos Estimados (MVP)

| Servicio | Estimado/mes | Notas |
|----------|-------------|-------|
| Bedrock | $5-20 | Depende de invocaciones |
| Lambda | < $5 | Free tier cubre mucho |
| EventBridge | < $1 | Pay per event |
| DynamoDB | < $5 | On-demand, bajo volumen |
| CloudWatch | $5-10 | Logs + métricas |
| ECS Fargate | $15-30 | 2-4 tasks pequeños |
| Amplify | $0-5 | Free tier generoso |
| **Total** | **$30-75/mes** | Para ambiente dev |
