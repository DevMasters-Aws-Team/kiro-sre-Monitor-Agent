"""Chat Router - Endpoint for Carmen Chat with Bedrock LLM."""

import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    """Request model for chat."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    context: Optional[str] = Field(None, description="Additional context (e.g., attached docs)")
    history: Optional[list[dict]] = Field(None, description="Chat history")


class ChatResponse(BaseModel):
    """Response model for chat."""
    response: str
    source: str  # "llm" or "fallback"
    model: Optional[str] = None


# System prompt for Carmen
SYSTEM_PROMPT = """Eres Carmen, una ingeniera SRE (Site Reliability Engineering) experta en AWS. 
Tu trabajo es ayudar a los ingenieros con:

1. **Diagnóstico de incidentes**: Analizas logs, métricas y alertas para encontrar la causa raíz.
2. **Remediación**: Sugieres acciones específicas para resolver problemas.
3. **Monitoreo**: Explicas cómo configurar alertas y dashboards.
4. **Arquitectura**: Aconsejas sobre mejores prácticas de arquitectura en AWS.

Características:
- Respondes en español
- Eres concisa y técnica
- Das respuestas accionables
- Usas formato markdown para mejor legibilidad
- Cuando no sabes algo, lo admites

Servicios que monitoreas:
- login-service (Autenticación)
- biometric-service (Biometría)
- product-service (Productos)
- inventory-service (Inventario)
- address-validation-service (Direcciones)
- purchase-service (Compras)
- sales-service (Ventas)
- email-service (Notificaciones)

Responde de forma breve y técnica. Si te preguntan sobre un servicio específico, 
proporciona diagnósticos basados en los logs y métricas disponibles."""


def _get_fallback_response(message: str) -> str:
    """Fallback response when LLM is not available."""
    message_lower = message.lower()
    
    # Simple keyword-based responses
    if any(word in message_lower for word in ["hola", "hello", "buenas"]):
        return """¡Hola! Soy Carmen, tu asistente SRE. 

Puedo ayudarte con:
- **Diagnóstico** de incidentes en microservicios
- **Análisis** de logs y métricas
- **Remediación** automática de problemas
- **Configuración** de monitoreo en AWS

¿En qué puedo ayudarte hoy?"""
    
    # Microservices count and status
    if any(word in message_lower for word in ["cuantos", "cuántos", "cantidad", "numeros", "número", "servicios", "microservicios", "activos", "monitoreando"]):
        return """## 📊 Microservicios Activos

Actualmente estamos monitoreando **8 microservicios**:

| # | Servicio | Estado | Latencia |
|---|----------|--------|----------|
| 1 | login-service | ✅ OK | 45ms |
| 2 | biometric-service | ⚠️ WARN | 520ms |
| 3 | product-service | ✅ OK | 65ms |
| 4 | inventory-service | ✅ OK | 80ms |
| 5 | address-validation-service | ✅ OK | 110ms |
| 6 | purchase-service | ✅ OK | 135ms |
| 7 | sales-service | ❌ DOWN | 3400ms |
| 8 | email-service | ✅ OK | 90ms |

### Resumen:
- ✅ **6 servicios** operativos (OK)
- ⚠️ **1 servicio** con advertencia (WARN)
- ❌ **1 servicio** caído (DOWN)

**Disponibilidad global**: 75%

¿Necesitas más detalles sobre algún servicio específico?"""
    
    if any(word in message_lower for word in ["status", "estado", "salud"]):
        return """## Estado del Sistema

| Servicio | Estado | Latencia |
|----------|--------|----------|
| login-service | ✅ OK | 45ms |
| biometric-service | ⚠️ WARN | 520ms |
| product-service | ✅ OK | 65ms |
| inventory-service | ✅ OK | 80ms |
| purchase-service | ✅ OK | 135ms |
| sales-service | ❌ DOWN | 3400ms |
| email-service | ✅ OK | 90ms |

**Recomendación**: El servicio `sales-service` está experimentando timeouts. 
¿Quieres que ejecute un reinicio automático?"""
    
    if any(word in message_lower for word in ["error", "fallo", "problema", "errores"]):
        return """## Análisis de Errores Recientes

He detectado los siguientes errores:

1. **DatabaseTimeoutError** en `sales-service`
   - Severidad: CRÍTICA
   - Acción recomendada: Reiniciar servicio
   
2. **PaymentGatewayTimeoutError** en `product-service`
   - Severidad: ALTA
   - Acción recomendada: Verificar conexión a BD

¿Quieres que ejecute alguna remediación automática?"""
    
    if any(word in message_lower for word in ["ayuda", "help", "que puedes", "qué puedes"]):
        return """## ¿Qué puedo hacer?

 Como ingeniera SRE virtual, puedo:

### 📊 Monitoreo
- Consultar estado de servicios
- Analizar métricas de latencia
- Revisar logs de errores

### 🔧 Remediación
- Reiniciar servicios caídos
- Escalar instancias bajo demanda
- Limpiar colas SQS stuck
- Invalidar cache de Redis

### 📝 Análisis
- Diagnosticar causa raíz de incidentes
- Correlacionar errores entre servicios
- Sugerir mejoras de arquitectura

### 🚀 Configuración
- Crear alertas de CloudWatch
- Configurar EventBridge rules
- Optimizar costos de AWS

¡Pregúntame lo que necesites!"""
    
    if any(word in message_lower for word in ["reiniciar", "restart", "reinicio"]):
        return """## 🔧 Reinicio de Servicios

Puedo reiniciar los siguientes servicios:

1. **sales-service** (❌ DOWN) - Recomendado
2. **biometric-service** (⚠️ WARN) - Opcional

¿Cuál quieres que reinicie?

**Nota**: El reinicio es seguro y no afecta otros servicios."""
    
    if any(word in message_lower for word in ["logs", "log", "registros"]):
        return """## 📋 Logs Recientes

Últimos logs de errores:

```
[ERROR] 2026-07-26 01:45:30 - sales-service
  DatabaseTimeoutError: Connection timeout
  
[ERROR] 2026-07-26 01:44:15 - product-service  
  PaymentGatewayTimeoutError: Gateway timeout
  
[WARN] 2026-07-26 01:43:00 - biometric-service
  High latency detected: 520ms
```

¿Quieres que analice algún log específico?"""
    
    # Default response with more context
    return f"""He recibido tu consulta: "{message}"

## 💡 Puedo ayudarte con:

### Preguntas frecuentes:
- **"¿Cuántos servicios tenemos?"** → Te muestro el estado actual
- **"¿Cuál es el estado del sistema?"** → Resumen de salud
- **"¿Qué errores hay?"** → Análisis de incidentes
- **"Reiniciar sales-service"** → Ejecuto remediación
- **"Muéstrame los logs"** → Logs recientes

### Comandos disponibles:
- `status` - Estado del sistema
- `errors` - Errores recientes
- `restart [servicio]` - Reiniciar servicio
- `logs` - Ver logs

¿Qué necesitas saber?"""


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with Carmen SRE Agent.
    
    Uses Bedrock (Claude) for intelligent responses, or fallback if not available.
    """
    from src.config import settings
    
    # Try to use LLM if not in mock mode
    if not settings.use_mock_aws:
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, _chat_with_llm, request.message, request.context, request.history
            )
            return ChatResponse(
                response=response,
                source="llm",
                model=settings.bedrock_model_id
            )
        except Exception as e:
            logger.error("LLM chat failed, using fallback: %s", str(e), exc_info=True)
    
    # Fallback response
    return ChatResponse(
        response=_get_fallback_response(request.message),
        source="fallback",
        model=None
    )


def _is_nova_model(model_id: str) -> bool:
    """Check if the model is an Amazon Nova model."""
    return model_id.startswith("amazon.") or model_id.startswith("us.amazon.")


def _build_nova_request(system_context: str, messages: list) -> dict:
    """Build request body for Amazon Nova models."""
    nova_messages = []
    for msg in messages:
        nova_messages.append({
            "role": msg["role"],
            "content": [{"text": msg["content"]}]
        })

    # Nova requires first message to be from "user" role
    # If history starts with "assistant", remove leading assistant messages
    while nova_messages and nova_messages[0]["role"] != "user":
        nova_messages.pop(0)

    return {
        "system": [{"text": system_context}],
        "messages": nova_messages,
        "inferenceConfig": {"maxTokens": 1024}
    }


def _build_claude_request(system_context: str, messages: list) -> dict:
    """Build request body for Anthropic Claude models."""
    # Claude requires first message to be from "user" role
    clean_messages = list(messages)
    while clean_messages and clean_messages[0]["role"] != "user":
        clean_messages.pop(0)

    return {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "system": system_context,
        "messages": clean_messages
    }


def _parse_response(response_body: dict, model_id: str) -> str:
    """Parse response from Bedrock model."""
    if _is_nova_model(model_id):
        return response_body["output"]["message"]["content"][0]["text"]
    else:
        return response_body["content"][0]["text"]


def _build_incident_context() -> str:
    """Construye el contexto de incidentes reales detectados por el webhook.

    Esto es lo que permite que Carmen sepa qué está fallando ahora mismo,
    en lugar de dar respuestas genéricas.
    """
    from src.agents.orchestrator import get_incident_summary, get_recent_incidents

    summary = get_incident_summary()
    if summary["total"] == 0:
        return (
            "\n\nESTADO ACTUAL DEL SISTEMA:\n"
            "No se han detectado incidentes en esta sesión. "
            "Todos los microservicios operan con normalidad."
        )

    lines = [
        "\n\nESTADO ACTUAL DEL SISTEMA (datos reales de esta sesión):",
        f"- Incidentes detectados: {summary['total']}",
        f"- Incidentes críticos/altos: {summary['critical_count']}",
        f"- Servicios afectados: {', '.join(summary['services_affected'])}",
        "- Errores por tipo: "
        + ", ".join(f"{k} ({v})" for k, v in summary["by_error_type"].items()),
        "",
        "ÚLTIMOS INCIDENTES ANALIZADOS:",
    ]

    for inc in get_recent_incidents(limit=5):
        lines.append(
            f"- [{inc['severity']}] {inc['service']} | {inc['error_type']} "
            f"| HTTP {inc['status_code']} | {inc['duration_ms']}ms\n"
            f"  Endpoint: {inc['endpoint'] or 'N/A'}\n"
            f"  Causa raíz: {inc['root_cause']}\n"
            f"  Decisión del agente: {inc['decision']} ({inc['decision_reason']})\n"
            f"  Trace ID: {inc['trace_id'] or 'N/A'} | Detectado: {inc['detected_at']}"
        )

    lines.append(
        "\nUsa estos datos reales para responder. Si te preguntan por fallos, "
        "reporta estos incidentes concretos con su causa raíz y la acción recomendada."
    )
    return "\n".join(lines)


def _chat_with_llm(message: str, context: str = None, history: list = None) -> str:
    """Use Bedrock to generate a response (supports Claude and Nova models)."""
    import boto3
    from src.config import settings

    model_id = settings.bedrock_model_id
    is_nova = _is_nova_model(model_id)

    logger.info("Invoking Bedrock - Model: %s (Nova=%s)", model_id, is_nova)
    logger.info("AWS Region: %s, Access Key present: %s", settings.aws_region, bool(settings.aws_access_key_id))

    # Build system context con el estado real del sistema
    system_context = SYSTEM_PROMPT + _build_incident_context()
    if context:
        system_context += f"\n\nContexto adicional: {context}"

    # Build messages
    messages = []
    if history:
        for msg in history[-6:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": message})

    # Build Bedrock client kwargs
    bedrock_kwargs = {"region_name": settings.aws_region}
    if settings.aws_access_key_id:
        bedrock_kwargs["aws_access_key_id"] = settings.aws_access_key_id
    if settings.aws_secret_access_key:
        bedrock_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    if settings.aws_session_token:
        bedrock_kwargs["aws_session_token"] = settings.aws_session_token

    bedrock = boto3.client("bedrock-runtime", **bedrock_kwargs)

    # Build request body based on model type
    if is_nova:
        request_body = _build_nova_request(system_context, messages)
    else:
        request_body = _build_claude_request(system_context, messages)

    logger.info("Invoking Bedrock model: %s", model_id)

    response = bedrock.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(request_body)
    )

    response_body = json.loads(response["body"].read())
    logger.info("Bedrock response received successfully")
    return _parse_response(response_body, model_id)


@router.post("/chat/test")
async def chat_test():
    """Test endpoint for chat."""
    from src.config import settings
    from src.agents.orchestrator import get_incident_summary

    return {
        "status": "ok",
        "message": "Chat endpoint is working",
        "llm_available": not settings.use_mock_aws,
        "model": settings.bedrock_model_id if not settings.use_mock_aws else None,
        "incidents_in_memory": get_incident_summary()["total"],
    }


@router.get("/incidents")
async def list_incidents(limit: int = 10):
    """Incidentes analizados por el agente en esta sesión.

    El Backend notifica cada error via POST /webhook; aquí se consulta
    el resultado de esos diagnósticos.
    """
    from src.agents.orchestrator import get_incident_summary, get_recent_incidents

    return {
        "summary": get_incident_summary(),
        "incidents": get_recent_incidents(limit=limit),
    }
