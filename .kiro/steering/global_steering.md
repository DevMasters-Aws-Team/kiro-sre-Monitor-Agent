# Global Steering - Kiro SRE Agent (Orquestador Principal)

## Stack Tecnológico
- **Lenguaje:** Python 3.12
- **LLM:** Amazon Bedrock (Claude/Titan)
- **Infraestructura como Código:** Terraform
- **Event Bus:** Amazon EventBridge
- **Observabilidad:** Amazon CloudWatch
- **Compute:** AWS Lambda (Skills) + ECS Fargate (Agent)
- **Auth:** AWS Cognito + IAM Roles

## Rol del Repositorio
Este es el "cerebro" del sistema Kiro. Aquí reside:
1. El orquestador principal (bucle de IA: Observe → Reason → Act)
2. Los prompts maestros de personalidad del agente
3. La infraestructura como código (Terraform)
4. Las reglas de EventBridge para disparar al agente
5. Los roles IAM y políticas de seguridad

## Estructura del Repositorio
```
kiro-agent/
├── .kiro/
│   └── steering/
│       ├── global_steering.md
│       ├── agent_prompts.md
│       ├── integrations.md
│       └── architecture_specs.md
├── terraform/
│   ├── main.tf                  # Provider + backend
│   ├── variables.tf             # Variables
│   ├── outputs.tf               # Outputs
│   ├── eventbridge.tf           # Event Bus + Rules
│   ├── cloudwatch.tf            # Log Groups + Alarms
│   ├── lambda.tf                # Skills Lambda functions
│   ├── iam.tf                   # Roles + Policies
│   ├── dynamodb.tf              # Tables
│   ├── cognito.tf               # User Pool + Auth
│   └── modules/
│       ├── monitoring/          # Módulo de monitoreo
│       └── remediation/         # Módulo de remediación
├── src/
│   ├── orchestrator.py          # Bucle principal del agente
│   ├── bedrock_client.py        # Cliente Amazon Bedrock
│   ├── event_handler.py         # Handler de eventos EventBridge
│   ├── decision_engine.py       # Motor de decisiones
│   └── prompts/
│       ├── system_prompt.md     # System prompt maestro
│       ├── diagnosis_prompt.md  # Prompt para diagnóstico
│       └── remediation_prompt.md # Prompt para remediación
├── tests/
│   ├── test_orchestrator.py
│   ├── test_decision_engine.py
│   └── test_event_handler.py
├── pyproject.toml
├── Dockerfile
└── Makefile
```

## Reglas Cognitivas del Agente

### Principio: Zero Falsos Positivos
El agente NUNCA debe:
- Actuar basándose en predicciones estadísticas
- Generar alertas por anomalías estimadas
- Tomar decisiones sin una métrica real confirmada

El agente SIEMPRE debe:
- Basarse en respuestas HTTP reales (500, 401, 503)
- Confirmar con métricas de CloudWatch en tiempo real
- Verificar que el error persiste antes de actuar (debounce 10s)

### Bucle de Pensamiento
```
OBSERVE:
  - Recibir evento de EventBridge
  - Obtener contexto de CloudWatch (logs + métricas)
  - Filtrar solo ERROR/WARN

REASON:
  - Analizar con Bedrock (LLM)
  - Identificar servicio, endpoint, error
  - Consultar base de conocimiento
  - Leer documentación del código si es necesario
  - Determinar: ¿error conocido o nuevo?

ACT:
  - Si conocido + confidence > 0.9 → Auto-remediar (ejecutar skill)
  - Si conocido + confidence < 0.9 → Sugerir + pedir confirmación
  - Si nuevo → Alertar equipo + crear ticket + sugerir solución
  - SIEMPRE registrar en audit trail
```

### Límites del Agente
1. **No puede** modificar infraestructura IAM
2. **No puede** eliminar bases de datos o buckets
3. **No puede** actuar sin métricas reales confirmadas
4. **Debe** pedir confirmación para acciones de risk HIGH
5. **Debe** registrar toda acción en el audit trail
6. **Máximo** 3 reintentos antes de escalar a humano

## Convenciones de Código
- Type hints obligatorios
- Docstrings en formato Google
- Logging estructurado (JSON) en toda operación
- Tests unitarios con moto (mocks AWS)
- Terraform formateado con `terraform fmt`
- Variables sensibles en AWS Secrets Manager (nunca hardcoded)
