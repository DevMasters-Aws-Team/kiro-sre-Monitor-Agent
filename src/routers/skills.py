"""
Skills Router — Exposición del catálogo de skills del Agente.
Permite al Frontend y a los evaluadores ver qué herramientas de remediación
tiene disponibles Carmen, con metadata completa de cada una.

GET /skills           → catálogo completo
POST /skills/{name}   → invocar una skill directamente (con guardas de seguridad)
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Skills"])

# ── Catálogo de Skills ──────────────────────────────────────────────────────

SKILLS_CATALOG: dict[str, dict[str, Any]] = {
    "restart_service": {
        "name": "restart_service",
        "display_name": "Reiniciar Servicio ECS",
        "description": (
            "Fuerza un nuevo deployment en ECS (forceNewDeployment=True). "
            "Útil cuando el servicio tiene un error persistente, memory leak "
            "o el container está en estado unhealthy."
        ),
        "trigger_conditions": [
            "HTTP 500 persistente (> 3 ocurrencias en 5 min)",
            "Error tipo DatabaseTimeoutError o PaymentGatewayTimeoutError",
            "Container en estado STOPPED inesperado",
        ],
        "iam_permissions": ["ecs:UpdateService", "ecs:DescribeServices"],
        "risk_level": "medium",
        "requires_confirmation": False,
        "params_schema": {
            "service_name": "string — nombre del servicio ECS (ej: payment-service)",
        },
        "example_params": {"service_name": "sales-service"},
        "implemented": True,
        "langchain_tool": True,
    },
    "scale_up": {
        "name": "scale_up",
        "display_name": "Escalar Servicio ECS",
        "description": (
            "Aumenta el desired count de tasks ECS para manejar mayor carga. "
            "Trigger típico: CPU > 80%, latencia P99 alta, o error rate > 5%."
        ),
        "trigger_conditions": [
            "Latencia promedio > 3000ms",
            "CPU utilization > 80% durante > 5 min",
            "Error rate > 5% del total de requests",
        ],
        "iam_permissions": ["ecs:UpdateService"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "params_schema": {
            "service_name": "string — nombre del servicio",
            "desired_count": "int — número deseado de tasks (default: 3)",
        },
        "example_params": {"service_name": "product-service", "desired_count": 3},
        "implemented": True,
        "langchain_tool": True,
    },
    "clear_cache": {
        "name": "clear_cache",
        "display_name": "Limpiar Caché Redis",
        "description": (
            "Elimina keys de caché de un servicio para forzar refresh de datos. "
            "Útil cuando hay datos stale, inconsistencias o BiometricServiceFailure."
        ),
        "trigger_conditions": [
            "Respuestas inconsistentes del servicio",
            "Error tipo BiometricServiceFailure",
            "Data stale detectada por el agente",
        ],
        "iam_permissions": [],
        "risk_level": "low",
        "requires_confirmation": False,
        "params_schema": {
            "service_name": "string — nombre del servicio cuyo caché se limpia",
        },
        "example_params": {"service_name": "biometric-service"},
        "implemented": True,
        "langchain_tool": True,
    },
    "purge_queue": {
        "name": "purge_queue",
        "display_name": "Purgar Cola SQS",
        "description": (
            "Purga todos los mensajes de una cola SQS. "
            "Usar cuando hay backpressure severo o mensajes corruptos atascados en DLQ."
        ),
        "trigger_conditions": [
            "Queue depth > umbral configurable",
            "Mensajes en DLQ creciendo sostenidamente",
            "Error tipo InventoryLockError persistente",
        ],
        "iam_permissions": ["sqs:PurgeQueue", "sqs:GetQueueAttributes"],
        "risk_level": "high",
        "requires_confirmation": True,
        "params_schema": {
            "queue_name": "string — nombre de la cola SQS (ej: inventory-svc-dlq)",
        },
        "example_params": {"queue_name": "inventory-svc-dlq"},
        "implemented": True,
        "langchain_tool": True,
    },
}


class SkillInvokeRequest(BaseModel):
    """Request para invocar una skill directamente."""
    params: dict[str, Any] = {}
    confirm: bool = False  # Para skills de alto riesgo


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/skills", summary="Catálogo de Skills de Remediación")
async def list_skills():
    """
    Retorna el catálogo completo de skills de remediación disponibles en el agente.

    Cada skill incluye: descripción, condiciones de activación, permisos IAM,
    nivel de riesgo y si requiere confirmación humana.
    """
    skills_list = list(SKILLS_CATALOG.values())
    implemented = sum(1 for s in skills_list if s["implemented"])

    return {
        "agent": "kiro-sre-monitor-agent",
        "version": "0.1.0",
        "total_skills": len(skills_list),
        "implemented_skills": implemented,
        "environment": settings.environment,
        "execution_mode": "mock" if settings.use_mock_aws else "live-aws",
        "skills": skills_list,
    }


@router.post("/skills/{skill_name}", summary="Invocar una Skill Directamente")
async def invoke_skill(skill_name: str, request: SkillInvokeRequest):
    """
    Invoca una skill de remediación directamente (bypaseando el análisis LLM).

    Para skills de alto riesgo (purge_queue, scale_up), `confirm=true` es obligatorio.
    En modo mock (KIRO_USE_MOCK_AWS=true), no se ejecutan operaciones reales en AWS.
    """
    if skill_name not in SKILLS_CATALOG:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_name}' not found. Available: {list(SKILLS_CATALOG.keys())}",
        )

    skill_meta = SKILLS_CATALOG[skill_name]

    # Guardia de seguridad para skills de alto riesgo
    if skill_meta["risk_level"] == "high" and not request.confirm:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Skill '{skill_name}' tiene risk_level=high. "
                "Envía confirm=true en el body para ejecutar. "
                f"Permisos IAM requeridos: {skill_meta['iam_permissions']}"
            ),
        )

    logger.info(
        "Skill invocada directamente: %s | params=%s | confirm=%s | mode=%s",
        skill_name,
        request.params,
        request.confirm,
        "mock" if settings.use_mock_aws else "live",
    )

    # Importar y ejecutar la skill via LangChain tool
    try:
        from src.skills import restart_service, scale_up, clear_cache, purge_queue

        skill_map = {
            "restart_service": restart_service.restart_service,
            "scale_up": scale_up.scale_up,
            "clear_cache": clear_cache.clear_cache,
            "purge_queue": purge_queue.purge_queue,
        }

        skill_fn = skill_map[skill_name]
        result = skill_fn.invoke(request.params)

        return {
            "skill": skill_name,
            "status": "executed",
            "mode": "mock" if settings.use_mock_aws else "live-aws",
            "params": request.params,
            "result": result,
            "risk_level": skill_meta["risk_level"],
            "iam_used": skill_meta["iam_permissions"],
        }

    except Exception as exc:
        logger.error("Error ejecutando skill %s: %s", skill_name, str(exc))
        raise HTTPException(status_code=500, detail=f"Skill execution failed: {str(exc)}")
