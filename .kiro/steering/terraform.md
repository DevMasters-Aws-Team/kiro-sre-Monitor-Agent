---
inclusion: fileMatch
fileMatchPattern: "terraform/**"
---

# Terraform IaC - Guía de Estructura y Mejores Prácticas

## Stack y Versiones
- **Terraform:** >= 1.5
- **Provider AWS:** ~> 5.0
- **Provider Archive:** ~> 2.7
- **Región principal:** us-east-1
- **Estado:** Local (terraform.tfstate)

## Convención de Nombres

### Recursos AWS
- Prefijo estándar: `local.prefix` = `"${var.project_name}-${var.environment}"`
- Formato: `${local.prefix}-<nombre-recurso>`
- Ejemplos: `kiro-monitor-dev-agent`, `kiro-monitor-dev-incidents`

### Archivos Terraform
- Un archivo por servicio/dominio AWS (no mezclar servicios en un mismo archivo)
- Nombres en minúsculas, singular: `lambda.tf`, `cognito.tf`, `s3.tf`
- Archivos base obligatorios:
  | Archivo | Propósito |
  |---------|-----------|
  | `versions.tf` | Versiones de Terraform y providers |
  | `provider.tf` | Configuración del provider (región, default_tags) |
  | `variables.tf` | Todas las variables de entrada |
  | `outputs.tf` | Todos los outputs |
  | `locals.tf` | Valores locales computados |
  | `main.tf` | Recursos principales o comentario placeholder |

### Recursos Terraform (resource names)
- snake_case en inglés: `aws_lambda_function.kiro_agent`
- Nombres descriptivos y cortos: `dashboard`, `frontend`, `artifacts`, `incidents`
- Si hay solo un recurso del tipo, usar nombre genérico del dominio

## Estructura de Archivos

```
terraform/
├── versions.tf          # required_version + required_providers
├── provider.tf          # provider "aws" con region + default_tags
├── variables.tf         # Variables de entrada (todas centralizadas)
├── outputs.tf           # Outputs (todos centralizados)
├── locals.tf            # locals { prefix = "..." }
├── main.tf              # Recursos principales o placeholder
├── iam.tf               # Roles + Policies + Attachments
├── lambda.tf            # Lambda functions + permissions
├── dynamodb.tf          # Tablas DynamoDB
├── eventbridge.tf       # Event Bus + Rules + Targets
├── cloudwatch.tf        # Log Groups + Alarms + Dashboards
├── cognito.tf           # User Pool + Clients + Domain
├── s3.tf                # Buckets + Policies + Lifecycle
├── ssm.tf               # Parameter Store entries
├── sns.tf               # Topics + Policies + Subscriptions
├── lambda/              # Código fuente de Lambdas
│   ├── index.py
│   └── requirements.txt
├── terraform.tfvars     # Valores de variables (NO commitear secretos)
├── terraform.tfstate    # Estado local
└── terraform.tfstate.backup
```

## Reglas para Agregar Nuevos Servicios

### 1. Crear archivo dedicado
Cada servicio AWS nuevo va en su propio archivo `<servicio>.tf`:
- `api_gateway.tf` para API Gateway
- `sqs.tf` para colas SQS
- `ecs.tf` para clusters ECS
- `rds.tf` para bases de datos RDS
- `waf.tf` para Web Application Firewall

### 2. Seguir el patrón de integración
Al agregar un servicio:
1. Crear el recurso en `<servicio>.tf`
2. Agregar permisos IAM en `iam.tf` (Statement adicional en la policy existente)
3. Agregar outputs en `outputs.tf`
4. Agregar variables necesarias en `variables.tf`
5. Si la Lambda necesita acceso, agregar environment variables en `lambda.tf`
6. Si hay configuración del agente, agregar parámetros en `ssm.tf`

### 3. Patrón de recurso estándar
```hcl
# <Servicio> - <Descripción breve>
# Free tier: <límites del free tier>

resource "aws_<tipo>" "<nombre>" {
  name = "${local.prefix}-<nombre-descriptivo>"
  
  # ... configuración ...
}
```

## Variables

### Convención
```hcl
variable "nombre_variable" {
  description = "Descripción clara del propósito"
  type        = string          # Siempre declarar tipo explícito
  default     = "valor"         # Default solo si tiene sentido
}
```

### Reglas
- Siempre declarar `type` explícito
- Siempre incluir `description`
- Usar `default` solo para valores que no cambian entre ambientes
- Variables sensibles: usar `sensitive = true`
- NO hardcodear ARNs, account IDs, o valores específicos de cuenta

## Outputs

### Convención
```hcl
output "nombre_descriptivo" {
  description = "Qué representa este output"
  value       = aws_recurso.nombre.atributo
}
```

### Reglas
- Exportar ARNs, IDs, y endpoints de todos los recursos principales
- Agrupar por servicio con comentarios separadores
- Formato: `<servicio>_<recurso>_<atributo>` (e.g., `cognito_user_pool_id`)

## IAM

### Patrón actual
- Un solo rol: `aws_iam_role.kiro_agent_role` (asumido por Lambda)
- Una sola policy: `aws_iam_policy.kiro_agent_policy` con múltiples Statements
- Cada Statement tiene `Sid` descriptivo

### Reglas de seguridad
- Nunca usar `Resource = "*"` en producción (aceptable en dev para logs/events)
- Usar ARNs específicos cuando sea posible
- Agregar `Sid` a cada Statement para identificarlo
- Para servicios nuevos: agregar un Statement dedicado, no mezclar con existentes
- Nunca dar permisos de eliminación destructiva (Delete*) al agente

## Tags

### Implementación actual
Tags automáticos via `default_tags` en el provider:
```hcl
default_tags {
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
```
- NO agregar estos tags manualmente en recursos (se duplicarían)
- Agregar tags adicionales específicos solo si son necesarios

## Free Tier / Optimización de Costos

### Principios
- Billing mode PAY_PER_REQUEST para DynamoDB (no provisioned capacity)
- Retention corto en logs (7 días para dev)
- Lifecycle rules para expirar objetos S3 (90 días)
- Memory mínima necesaria en Lambda (256MB para el agente)
- Evitar recursos que generen costo fijo (NAT Gateway, RDS multi-AZ, etc.)

### Límites Free Tier actuales (a considerar)
| Servicio | Límite gratuito |
|----------|----------------|
| Lambda | 1M requests/mes, 400K GB-seconds |
| DynamoDB | 25GB storage, 25 WCU/RCU |
| S3 | 5GB, 20K GET, 2K PUT |
| SNS | 1M publishes, 1K emails |
| SSM Parameters | 10K standard parameters |
| Cognito | 50K MAU |
| CloudWatch | 10 alarms, 5GB logs ingestion |
| EventBridge | todos los eventos de AWS services gratis |

## State Management

### Actual: Estado local
- Archivo: `terraform/terraform.tfstate`
- Backup: `terraform/terraform.tfstate.backup`
- **NO commitear** el tfstate a Git (agregar a .gitignore)

### Futuro: Migrar a S3 backend
```hcl
backend "s3" {
  bucket = "kiro-terraform-state"
  key    = "kiro-agent/terraform.tfstate"
  region = "us-east-1"
}
```

## Comandos de Trabajo

```bash
cd terraform
terraform fmt -recursive      # Formatear antes de commit
terraform validate            # Validar sintaxis
terraform plan               # Preview de cambios
terraform apply              # Aplicar cambios
terraform plan -destroy      # Preview de destrucción (CUIDADO)
```

## Anti-patrones a Evitar

1. **NO** mezclar múltiples servicios en un solo .tf (excepto si están estrechamente acoplados)
2. **NO** hardcodear account IDs o ARNs completos
3. **NO** usar `terraform destroy` sin revisar el plan primero
4. **NO** crear recursos sin outputs
5. **NO** agregar permisos sin Sid descriptivo
6. **NO** usar provisioned capacity cuando on-demand es suficiente
7. **NO** crear módulos prematuramente (solo cuando haya reutilización real)
8. **NO** usar `count` cuando `for_each` es más legible
9. **NO** commitear `terraform.tfstate` o `terraform.tfvars` con secretos

## Checklist para Nuevo Recurso

- [ ] Archivo `.tf` dedicado creado
- [ ] Nombre con prefijo `local.prefix`
- [ ] Permisos IAM agregados en `iam.tf`
- [ ] Outputs agregados en `outputs.tf`
- [ ] Variables en `variables.tf` (si aplica)
- [ ] Environment vars en Lambda (si aplica)
- [ ] Parámetros SSM (si es configuración del agente)
- [ ] `terraform fmt` aplicado
- [ ] `terraform validate` pasa
- [ ] `terraform plan` revisado (sin destrucciones inesperadas)
- [ ] Documentación de free tier considerada
