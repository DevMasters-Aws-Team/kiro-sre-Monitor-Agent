# Requirements — Kiro SRE Monitor Agent (Carmen)

## Introduction

El Agente Carmen es un SRE autónomo impulsado por Amazon Bedrock (Nova Lite / Claude). Monitorea microservicios de e-commerce en tiempo real mediante CloudWatch, diagnostica incidentes con IA, y ejecuta skills de remediación automática. Expone un chat conversacional que permite a los ingenieros interactuar con el sistema en lenguaje natural.

El proyecto implementa el flujo completo del hackathon: **MCP → Skills → Hooks → Powers → AWS → Git + PRs**.

## Glossary

| Término | Definición |
|---------|-----------|
| Observe→Reason→Act | Bucle cognitivo del agente: recopila contexto, diagnostica con LLM, actúa |
| Skill | Función de remediación automatizada (`@tool` de LangChain) |
| Knowledge Base | Tabla DynamoDB con errores conocidos y sus soluciones históricas |
| Audit Trail | Registro inmutable en DynamoDB de cada acción ejecutada |
| MCP | Model Context Protocol — protocolo de herramientas para el IDE Kiro |
| Decision Engine | Motor de reglas que decide la acción cuando Bedrock no está disponible |
| Webhook | POST entrante del Backend cuando detecta un error de nivel ERROR |
| Confidence | Nivel de certeza del diagnóstico (0.0–1.0) calculado por el LLM o Decision Engine |

## Requirement 1: Recepción y Procesamiento de Alertas (Observe)

**User Story:** Como agente SRE autónomo, quiero recibir alertas automáticas del Backend cuando se detecte un error en producción, para iniciar el diagnóstico sin esperar intervención humana.

### Acceptance Criteria

1. WHEN el Backend hace POST `/webhook` con `state = "ALARM"`, THE agente SHALL procesar la alerta en el ciclo Observe→Reason→Act
2. THE endpoint `/webhook` SHALL validar el schema `CloudWatchAlert` con los campos obligatorios: `alarm_name`, `state`, `reason`, `dimensions`
3. IF el payload es inválido, THEN el sistema SHALL retornar HTTP 422 con detalle del campo faltante
4. THE endpoint `/webhook/chaos` SHALL permitir simular incidentes con diferentes tipos de error para testing
5. WHEN `state = "OK"`, THE agente SHALL retornar respuesta con `status = "ignored"` sin ejecutar el ciclo

## Requirement 2: Diagnóstico con IA (Reason)

**User Story:** Como equipo SRE, quiero que el agente use Amazon Bedrock para analizar la causa raíz de incidentes usando el contexto real de logs, para obtener diagnósticos precisos en segundos.

### Acceptance Criteria

1. WHEN se procesa una alerta, THE agente SHALL obtener logs recientes del servicio afectado desde CloudWatch o el Backend local
2. THE diagnóstico SHALL incluir: `root_cause`, `affected_component`, `error_category`, `is_known`, `confidence`, `severity`
3. IF Bedrock está disponible (`KIRO_USE_MOCK_AWS=false`), THEN el diagnóstico SHALL usar el LLM con el prompt maestro de Carmen
4. IF Bedrock no responde, THEN el Decision Engine SHALL generar un diagnóstico basado en reglas predefinidas
5. THE agente SHALL soportar múltiples modelos: Nova Lite, Nova Pro, Claude Haiku, Claude Sonnet — sin cambios de código

## Requirement 3: Remediación Automática (Act)

**User Story:** Como ingeniero de guardia, quiero que el agente ejecute automáticamente acciones de bajo riesgo y solicite confirmación para las de alto riesgo, para reducir el MTTR sin comprometer la estabilidad.

### Acceptance Criteria

1. WHERE `confidence >= 0.8` AND `risk_level != "high"`, THE agente SHALL ejecutar la skill automáticamente vía LangChain `@tool`
2. WHERE `risk_level = "high"` OR `requires_confirmation = true`, THE agente SHALL retornar `status = "requires_confirmation"` sin ejecutar
3. WHERE `confidence < 0.7` OR `action = "suggest"`, THE agente SHALL retornar `status = "escalate"` con la recomendación
4. THE sistema SHALL registrar cada ejecución en DynamoDB AuditTable cuando `KIRO_ENABLE_AUDIT_TRAIL = true`
5. THE agente SHALL exponer `GET /skills` con el catálogo completo de skills y su metadata

## Requirement 4: Chat Conversacional con Carmen

**User Story:** Como ingeniero SRE, quiero chatear con Carmen en lenguaje natural para consultar el estado del sistema y los incidentes recientes, sin necesitar conocer los endpoints de la API.

### Acceptance Criteria

1. POST `/chat` SHALL aceptar mensajes en español o inglés y retornar respuesta de Bedrock
2. THE respuesta SHALL indicar la fuente: `"llm"` (Bedrock activo) o `"fallback"` (modo mock/sin credenciales)
3. WHEN se consulta sobre incidentes, THE chat SHALL usar el `INCIDENT_HISTORY` en memoria del orquestador para dar respuestas contextualizadas con datos reales
4. POST `/chat/test` SHALL verificar la conectividad con Bedrock y retornar `llm_available: true/false`
5. GET `/incidents` SHALL retornar los últimos N incidentes analizados en la sesión actual

## Requirement 5: Infraestructura como Código (Powers)

**User Story:** Como equipo DevOps, quiero que toda la infraestructura AWS esté definida en Terraform con principio de Least Privilege, para reproducir el entorno en cualquier cuenta AWS.

### Acceptance Criteria

1. THE Terraform SHALL provisionar: DynamoDB (3 tablas), EventBridge (bus + rules), CloudWatch (log groups + alarms), Lambda (orchestrator + skills), IAM (roles restrictivos), Cognito (user pool), SNS (alertas), S3 (state backend)
2. THE IAM roles SHALL seguir el principio de Least Privilege — ningún rol con `"*"` en actions sin condition
3. THE credenciales sensibles SHALL almacenarse en AWS SSM Parameter Store, nunca en el código
4. `terraform plan` SHALL ejecutar sin errores antes de cualquier `apply`

## Correctness Properties

- **P1 (Zero False Positives):** El agente NUNCA ejecuta una skill sin una alerta real confirmada (HTTP 500, 503, timeout)
- **P2 (LLM Fallback):** Si Bedrock no responde, el Decision Engine provee diagnóstico básico — el sistema nunca retorna 500
- **P3 (Audit Completeness):** Cada skill ejecutada tiene exactamente un registro en AuditTable
- **P4 (Schema Validation):** Todo payload entrante es validado con Pydantic antes de procesarse
- **P5 (Retry Safety):** La misma alerta procesada dos veces produce el mismo resultado (idempotencia del análisis)
