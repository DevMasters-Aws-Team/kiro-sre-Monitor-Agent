"""Agente SRE Autónomo - Orquestador principal.

Recibe alertas de CloudWatch, las analiza con LangChain create_agent
y ejecuta acciones de remediación cuando es necesario.

Soporta:
  - Múltiples proveedores de modelo (KIRO_MODEL_ID)
  - Tools locales (skills/) + tools remotas via MCP (mcp_servers.json)
"""

import logging
import uuid

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from src.adapters.mcp_adapter import MCPAdapter
from src.agents.llm_provider import get_model
from src.agents.sre_autonomo.prompts import SYSTEM_PROMPT
from src.config import settings
from src.models.alerts import CloudWatchAlert, WebhookResponse
from src.skills.clear_cache import clear_cache
from src.skills.purge_queue import purge_queue
from src.skills.restart_service import restart_service
from src.skills.scale_up import scale_up

logger = logging.getLogger(__name__)

# Tools locales (skills del agente SRE)
LOCAL_TOOLS = [restart_service, scale_up, clear_cache, purge_queue]

# Checkpointer para mantener estado de conversación
checkpointer = InMemorySaver()

# Adaptador MCP (singleton para reutilizar conexiones)
_mcp_adapter = MCPAdapter()


async def _build_agent():
    """Construye el agente SRE Autónomo con create_agent.

    Combina las tools locales (skills/) con las tools remotas
    obtenidas de servidores MCP configurados en mcp_servers.json.
    """
    model = get_model()

    # Combinar tools locales + MCP tools
    all_tools = list(LOCAL_TOOLS)

    if _mcp_adapter.is_configured:
        mcp_tools = await _mcp_adapter.get_tools()
        all_tools.extend(mcp_tools)
        logger.info(
            "Agente construido con %d tools locales + %d tools MCP",
            len(LOCAL_TOOLS),
            len(mcp_tools),
        )
    else:
        logger.info("Agente construido con %d tools locales (sin MCP)", len(LOCAL_TOOLS))

    agent = create_agent(
        model=model,
        tools=all_tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    return agent


def _format_alert_message(alert: CloudWatchAlert) -> str:
    """Formatea la alerta como mensaje para el agente."""
    return (
        f"Analiza la siguiente alerta de CloudWatch:\n\n"
        f"**Alarma**: {alert.alarm_name}\n"
        f"**Estado**: {alert.state} (anterior: {alert.previous_state or 'N/A'})\n"
        f"**Razón**: {alert.reason}\n"
        f"**Namespace**: {alert.namespace or 'N/A'}\n"
        f"**Métrica**: {alert.metric_name or 'N/A'}\n"
        f"**Dimensiones**: {alert.dimensions}\n"
        f"**Timestamp**: {alert.timestamp.isoformat()}\n\n"
        f"Proporciona tu análisis completo y ejecuta las acciones de remediación necesarias."
    )


async def analyze_alert(alert: CloudWatchAlert) -> WebhookResponse:
    """Recibe una alerta de CloudWatch y la analiza con el Agente SRE Autónomo."""
    alert_id = str(uuid.uuid4())

    logger.info(
        "Agente SRE Autónomo procesando alerta: %s | Estado: %s",
        alert.alarm_name,
        alert.state,
    )

    agent = await _build_agent()
    message = _format_alert_message(alert)

    try:
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": message}]},
            config={"configurable": {"thread_id": alert_id}},
        )

        # Extraer la respuesta final del agente
        messages = result.get("messages", [])
        last_message = messages[-1] if messages else None

        if last_message and hasattr(last_message, "content"):
            analysis = last_message.content
        else:
            analysis = "Sin análisis disponible"

        # Extraer tools ejecutadas
        actions_executed = [
            msg.name for msg in messages if hasattr(msg, "name") and msg.name
        ]

    except Exception as e:
        logger.error("Error en el Agente SRE Autónomo: %s", str(e))
        analysis = f"Error durante el análisis: {str(e)}"
        actions_executed = []

    return WebhookResponse(
        status="analyzed",
        alert_id=alert_id,
        analysis=analysis,
        actions_suggested=actions_executed,
    )
