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


from src.routers.prompts import (
    CARMEN_SYSTEM_PROMPT,
    SALUDOS_SIMPLES,
    FALLBACK_GREETING,
    FALLBACK_OFFLINE,
)


def _get_fallback_response(message: str) -> str:
    """Fallback response when LLM is not available."""
    return FALLBACK_OFFLINE


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with Carmen SRE Agent.
    
    Uses Bedrock (Claude/Nova) for intelligent responses, or fallback if not available.
    """
    from src.config import settings
    
    # Optimización de Recursos y Tokens: Pre-filtro de saludos y charla básica
    message_clean = request.message.lower().strip(" ?,.¡!¿")
    if message_clean in SALUDOS_SIMPLES:
        return ChatResponse(
            response=FALLBACK_GREETING,
            source="fallback",
            model=None
        )
    
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
            f"  Causa raiz: {inc['root_cause']}\n"
            f"  Recomendacion: {inc['decision_reason']}\n"
            f"  Trace ID: {inc['trace_id'] or 'N/A'} | Detectado: {inc['detected_at']}"
        )

    lines.append(
        "\nUsa estos datos reales para responder. Si te preguntan por fallos, "
        "reporta estos incidentes concretos con su causa raíz y la acción recomendada."
    )
    return "\n".join(lines)


def _is_greeting(message: str) -> bool:
    """Detecta si un mensaje es un saludo conversacional simple."""
    clean = message.lower().strip(" ?,.¡!¿")
    words = {"hola", "buenas", "buenos", "buen", "tardes", "noches", "tal", "como", "cómo", "hello", "hi", "hey"}
    tokens = [t for t in clean.split() if t]
    if len(tokens) <= 3 and any(t in words for t in tokens):
        return True
    return False


def _chat_with_llm(message: str, context: str = None, history: list = None) -> str:
    """Use Bedrock to generate a response (supports Claude and Nova models)."""
    import boto3
    from src.config import settings

    model_id = settings.bedrock_model_id
    is_nova = _is_nova_model(model_id)

    logger.info("Invoking Bedrock - Model: %s (Nova=%s)", model_id, is_nova)
    logger.info("AWS Region: %s, Access Key present: %s", settings.aws_region, bool(settings.aws_access_key_id))

    # Build system context con el estado real del sistema (solo si NO es un saludo simple)
    if _is_greeting(message):
        system_context = CARMEN_SYSTEM_PROMPT + "\n\n(El usuario te esta saludando de manera sencilla. Brinda un saludo muy amable, amigable, corto y profesional en español, de maximo 2 lineas, presentandote brevemente y preguntandole en que puedes asistir hoy con la observabilidad de sus microservicios, sin listar ningun incidente ni log de forma predeterminada)."
    else:
        system_context = CARMEN_SYSTEM_PROMPT + _build_incident_context()
        
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