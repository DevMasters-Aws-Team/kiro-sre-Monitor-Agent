# Integrations - Kiro SRE Agent

## Definición
Las integraciones definen cómo el agente Kiro se conecta con los servicios AWS para el flujo Observe → Reason → Act.

## 1. Amazon EventBridge (Trigger del Agente)

### Event Bus Configuration
```json
{
  "EventBusName": "kiro-monitor-events",
  "Description": "Bus de eventos para el agente Kiro SRE"
}
```

### Event Rules (Cuándo despertar a Kiro)

#### Rule 1: CloudWatch Alarm State Change
```json
{
  "Name": "kiro-alarm-trigger",
  "Description": "Dispara a Kiro cuando una alarma cambia a estado ALARM",
  "EventPattern": {
    "source": ["aws.cloudwatch"],
    "detail-type": ["CloudWatch Alarm State Change"],
    "detail": {
      "state": {
        "value": ["ALARM"]
      },
      "alarmName": [{
        "prefix": "kiro-"
      }]
    }
  },
  "Targets": [{
    "Arn": "arn:aws:lambda:us-east-1:*:function:kiro-orchestrator",
    "Id": "kiro-orchestrator-target"
  }]
}
```

#### Rule 2: ECS Task State Change
```json
{
  "Name": "kiro-ecs-failure",
  "Description": "Dispara a Kiro cuando un task ECS falla",
  "EventPattern": {
    "source": ["aws.ecs"],
    "detail-type": ["ECS Task State Change"],
    "detail": {
      "lastStatus": ["STOPPED"],
      "stoppedReason": [{
        "anything-but": ["Scaling activity initiated by"]
      }]
    }
  },
  "Targets": [{
    "Arn": "arn:aws:lambda:us-east-1:*:function:kiro-orchestrator",
    "Id": "kiro-ecs-target"
  }]
}
```

#### Rule 3: Custom Application Errors
```json
{
  "Name": "kiro-app-error",
  "Description": "Dispara a Kiro cuando la aplicación emite un evento de error",
  "EventPattern": {
    "source": ["kiro.microservices"],
    "detail-type": ["ApplicationError"],
    "detail": {
      "severity": ["ERROR", "CRITICAL"],
      "statusCode": [500, 503, 401]
    }
  },
  "Targets": [{
    "Arn": "arn:aws:lambda:us-east-1:*:function:kiro-orchestrator",
    "Id": "kiro-app-error-target"
  }]
}
```

## 2. Amazon CloudWatch (Observabilidad)

### Log Groups Monitoreados
```
/ecs/kiro-user-service        → Logs del servicio de usuarios
/ecs/kiro-order-service       → Logs del servicio de órdenes
/ecs/kiro-payment-service     → Logs del servicio de pagos
/ecs/kiro-auth-service        → Logs del servicio de auth
/kiro/agent                   → Logs propios del agente
```

### Alarmas de CloudWatch

#### Alarm: High Error Rate
```json
{
  "AlarmName": "kiro-high-error-rate",
  "MetricName": "5XXError",
  "Namespace": "AWS/ApplicationELB",
  "Statistic": "Sum",
  "Period": 60,
  "EvaluationPeriods": 2,
  "Threshold": 5,
  "ComparisonOperator": "GreaterThanThreshold",
  "AlarmActions": ["arn:aws:sns:us-east-1:*:kiro-alerts"]
}
```

#### Alarm: High Latency
```json
{
  "AlarmName": "kiro-high-latency",
  "MetricName": "TargetResponseTime",
  "Namespace": "AWS/ApplicationELB",
  "Statistic": "p99",
  "Period": 60,
  "EvaluationPeriods": 3,
  "Threshold": 2.0,
  "ComparisonOperator": "GreaterThanThreshold"
}
```

#### Alarm: Service Down
```json
{
  "AlarmName": "kiro-service-down",
  "MetricName": "HealthyHostCount",
  "Namespace": "AWS/ApplicationELB",
  "Statistic": "Minimum",
  "Period": 60,
  "EvaluationPeriods": 1,
  "Threshold": 1,
  "ComparisonOperator": "LessThanThreshold"
}
```

### Metric Filters (Para logs estructurados)
```json
{
  "FilterName": "kiro-error-count",
  "LogGroupName": "/ecs/kiro-*",
  "FilterPattern": "{ $.level = \"ERROR\" }",
  "MetricTransformations": [{
    "MetricName": "ApplicationErrorCount",
    "MetricNamespace": "Kiro/Microservices",
    "MetricValue": "1"
  }]
}
```

## 3. Amazon Bedrock (Razonamiento)

### Configuración del Cliente
```python
import boto3
import json

class BedrockClient:
    def __init__(self, region: str = 'us-east-1'):
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=region
        )
        self.model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
    
    async def invoke(self, system_prompt: str, user_message: str) -> dict:
        """Invoca Bedrock para razonamiento"""
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "temperature": 0.1,
                "system": system_prompt,
                "messages": [{
                    "role": "user",
                    "content": user_message
                }]
            })
        )
        return json.loads(response['body'].read())
```

### Flujo de Invocación
```
EventBridge Event
       │
       ▼
Lambda: kiro-orchestrator
       │
       ├── 1. Obtener contexto (CloudWatch logs + métricas)
       ├── 2. Filtrar logs (solo ERROR/WARN)
       ├── 3. Consultar Knowledge Base (DynamoDB)
       ├── 4. Construir prompt con contexto
       ├── 5. Invocar Bedrock (diagnóstico)
       ├── 6. Parsear respuesta JSON
       ├── 7. Decidir acción (auto/confirm/escalate)
       ├── 8. Ejecutar skill si aplica
       └── 9. Registrar resultado (audit + dashboard)
```

## 4. AWS Lambda (Skills de Remediación)

### Lambda Functions
| Función | Runtime | Timeout | Memory | Trigger |
|---------|---------|---------|--------|---------|
| kiro-orchestrator | Python 3.12 | 60s | 512MB | EventBridge |
| kiro-restart-service | Python 3.12 | 30s | 256MB | Orchestrator |
| kiro-scale-up | Python 3.12 | 30s | 256MB | Orchestrator |
| kiro-purge-queue | Python 3.12 | 15s | 128MB | Orchestrator |
| kiro-send-alert | Python 3.12 | 10s | 128MB | Orchestrator |

### Invocación de Skills desde el Orquestador
```python
async def invoke_skill(skill_name: str, params: dict) -> dict:
    """Invoca una skill Lambda"""
    lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
        FunctionName=f'kiro-{skill_name}',
        InvocationType='RequestResponse',
        Payload=json.dumps(params)
    )
    return json.loads(response['Payload'].read())
```

## 5. AWS Cognito (Autenticación Dashboard)

### User Pool Configuration
```json
{
  "UserPoolName": "kiro-dashboard-users",
  "Policies": {
    "PasswordPolicy": {
      "MinimumLength": 8,
      "RequireUppercase": true,
      "RequireLowercase": true,
      "RequireNumbers": true
    }
  },
  "AutoVerifiedAttributes": ["email"],
  "UsernameAttributes": ["email"]
}
```

### App Client
```json
{
  "ClientName": "kiro-dashboard-web",
  "ExplicitAuthFlows": [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ],
  "SupportedIdentityProviders": ["COGNITO"]
}
```

## Diagrama de Integración Completo

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│Microsvcs │────▶│  CloudWatch  │────▶│  EventBridge │
│(ECS)     │     │  Logs+Alarms │     │  Event Bus   │
└──────────┘     └──────────────┘     └──────┬───────┘
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │  Lambda:         │
                                    │  kiro-orchestrator│
                                    └────────┬─────────┘
                                             │
                    ┌────────────────────────┼────────────────────┐
                    │                        │                    │
                    ▼                        ▼                    ▼
          ┌──────────────┐        ┌──────────────┐     ┌──────────────┐
          │   Bedrock    │        │   DynamoDB   │     │   Lambda     │
          │   (Reason)   │        │   (Knowledge)│     │   (Skills)   │
          └──────────────┘        └──────────────┘     └──────────────┘
                                                                │
                                                                ▼
                                                       ┌──────────────┐
                                                       │  SNS/SES     │
                                                       │  (Alertas)   │
                                                       └──────────────┘
```
