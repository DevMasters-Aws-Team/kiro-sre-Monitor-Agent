"""Orchestrator - Bucle principal del agente SRE (Observe → Reason → Act)."""

import logging
import uuid
from collections import deque
from datetime import datetime, timedelta
from typing import Any

from src.agents.decision_engine import (
    DecisionEngine,
    RemediationAction,
    RemediationDecision,
    Severity,
    decision_engine,
)
from src.agents.llm_provider import get_llm
from src.agents.sre_autonomo.prompts import SYSTEM_PROMPT
from src.config import settings
from src.infrastructure.clients import aws_clients
from src.models.alerts import CloudWatchAlert, WebhookResponse
from src.skills.clear_cache import clear_cache
from src.skills.purge_queue import purge_queue
from src.skills.restart_service import restart_service
from src.skills.scale_up import scale_up

logger = logging.getLogger(__name__)

# Tools disponibles para el agente
AGENT_TOOLS = [restart_service, scale_up, clear_cache, purge_queue]

# Historial de incidentes analizados (en memoria).
# Permite que el chat de Carmen conozca los errores que el webhook ya diagnosticó.
INCIDENT_HISTORY: deque = deque(maxlen=50)


class Orchestrator:
    """Orquestador principal del agente SRE."""

    def __init__(self):
        self.decision_engine = decision_engine
        self._agent = None

    def _build_agent(self):
        """Construye el agente SRE Autónomo con create_agent."""
        from langchain.agents import create_agent

        model_string = f"bedrock_converse:{settings.bedrock_model_id}"

        agent = create_agent(
            model=model_string,
            tools=AGENT_TOOLS,
            system_prompt=SYSTEM_PROMPT,
        )

        return agent

    async def process_alert(self, alert: CloudWatchAlert) -> WebhookResponse:
        """Procesa una alerta de CloudWatch usando el bucle Observe→Reason→Act."""
        alert_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        logger.info(
            "Orchestrator procesando alerta: %s | Estado: %s",
            alert.alarm_name,
            alert.state,
        )

        # OBSERVE: Obtener contexto
        context = await self._observe(alert)

        # REASON: Diagnosticar con LLM + Decision Engine
        diagnosis, decision = await self._reason(alert, context)

        # ACT: Ejecutar remediación si es seguro
        actions_executed = await self._act(decision)

        # Registrar en audit trail
        await self._audit_trail(alert_id, alert, diagnosis, decision, actions_executed)

        # Construir respuesta
        analysis = self._build_analysis(diagnosis, decision, actions_executed)
        actions_suggested = [a.value for a in actions_executed] if actions_executed else []

        # Guardar en el historial en memoria para que el chat lo conozca
        self._record_incident(alert_id, alert, diagnosis, decision, actions_executed, start_time)

        return WebhookResponse(
            status="analyzed",
            alert_id=alert_id,
            analysis=analysis,
            actions_suggested=actions_suggested,
        )

    def _record_incident(
        self,
        alert_id: str,
        alert: CloudWatchAlert,
        diagnosis: dict,
        decision: RemediationDecision,
        actions: list[RemediationAction],
        detected_at: datetime,
    ) -> None:
        """Guarda el incidente en el historial en memoria (consultable desde el chat)."""
        diag = diagnosis.get("diagnosis")
        INCIDENT_HISTORY.appendleft(
            {
                "alert_id": alert_id,
                "detected_at": detected_at.isoformat(),
                "service": alert.dimensions.get("ServiceName", "unknown"),
                "endpoint": alert.raw_payload.get("endpoint", ""),
                "error_type": alert.raw_payload.get("error_type", "Unknown"),
                "status_code": alert.raw_payload.get("status_code", 0),
                "duration_ms": alert.raw_payload.get("duration_ms", 0),
                "trace_id": alert.raw_payload.get("trace_id", ""),
                "message": alert.reason,
                "root_cause": getattr(diag, "root_cause", "N/A"),
                "severity": getattr(diag, "severity", None).value if getattr(diag, "severity", None) else "UNKNOWN",
                "confidence": getattr(diag, "confidence", 0.0),
                "is_known": getattr(diag, "is_known", False),
                "decision": decision.action.value,
                "decision_reason": decision.reason,
                "actions_executed": [a.value for a in actions],
                "llm_used": diagnosis.get("llm_used", False),
            }
        )


    async def _observe(self, alert: CloudWatchAlert) -> dict[str, Any]:
        """Fase de observación: obtiene contexto de CloudWatch y logs."""
        context = {
            "alert": alert,
            "recent_logs": [],
            "metrics": {},
        }

        service_name = alert.dimensions.get("ServiceName", "")
        if not service_name:
            return context

        # Ventana de búsqueda: últimos 15 minutos
        start_time = int((datetime.utcnow() - timedelta(minutes=15)).timestamp() * 1000)

        try:
            response = aws_clients.cloudwatch_logs.filter_log_events(
                logGroupName=settings.log_group_name,
                # Búsqueda de texto simple: el patrón JSON de CloudWatch no acepta ':'
                filterPattern=f'"{service_name}"',
                startTime=start_time,
                limit=20,
            )
            events = response.get("events", [])
            context["recent_logs"] = events
            logger.info(
                "Observe: %d logs recuperados de CloudWatch para %s",
                len(events),
                service_name,
            )
        except Exception as e:
            logger.warning("No se pudieron obtener logs de CloudWatch: %s", str(e))

        # Fallback: Si no se recuperaron logs de CloudWatch (o estamos en desarrollo/mock),
        # consultar directamente al backend local para obtener logs estructurados rápidos.
        if not context["recent_logs"]:
            try:
                import httpx
                backend_url = "http://localhost:8000/api/logs"
                logger.info("Intentando recuperar logs resumidos desde el backend local: %s", backend_url)
                
                async with httpx.AsyncClient() as client:
                    resp = await client.get(backend_url, timeout=3.0)
                    if resp.status_code == 200:
                        all_logs = resp.json()
                        # Filtrar logs para el microservicio específico
                        filtered = [
                            {
                                "timestamp": int(datetime.utcnow().timestamp() * 1000),
                                "message": f"[{log.get('level', 'INFO')}] {log.get('msg', '')} (service={log.get('service')}, method={log.get('method')}, status={log.get('status')})"
                            }
                            for log in all_logs if log.get("service") == service_name
                        ]
                        context["recent_logs"] = filtered[:20]
                        logger.info(
                            "Observe (Fallback Backend): %d logs locales recuperados para %s",
                            len(filtered),
                            service_name,
                        )
            except Exception as ex:
                logger.warning("No se pudieron recuperar logs de fallback del backend: %s", str(ex))

        return context

    async def _reason(
        self, alert: CloudWatchAlert, context: dict[str, Any]
    ) -> tuple[dict, RemediationDecision]:
        """Fase de razonamiento: diagnostica con LLM (Bedrock) y decide acción."""
        from src.config import settings
        
        # Extraer información de la alerta
        service = alert.dimensions.get("ServiceName", "unknown")
        error_type = alert.raw_payload.get("error_type", "InternalServerError")
        status_code = alert.raw_payload.get("status_code", 500)
        error_message = alert.reason
        duration_ms = alert.raw_payload.get("duration_ms", 0)

        # Intentar usar LLM (Bedrock) si no está en mock mode
        llm_diagnosis = None
        if not settings.use_mock_aws:
            try:
                llm_diagnosis = await self._reason_with_llm(alert, context)
                logger.info("LLM (Bedrock) procesó la alerta exitosamente")
            except Exception as e:
                logger.warning("Error usando LLM, fallback a decision engine: %s", str(e))

        # Si el LLM no respondió, usar decision engine (fallback)
        if not llm_diagnosis:
            diagnosis = self.decision_engine.diagnose(
                service=service,
                endpoint=alert.namespace or "unknown",
                status_code=status_code,
                error_type=error_type,
                error_message=error_message,
                duration_ms=duration_ms,
            )
        else:
            diagnosis = llm_diagnosis

        # Decidir acción
        decision = self.decision_engine.decide_action(diagnosis, error_type)

        logger.info(
            "Diagnóstico: severidad=%s, confianza=%.2f, acción=%s, LLM=%s",
            diagnosis.severity.value,
            diagnosis.confidence,
            decision.action.value,
            "Sí" if llm_diagnosis else "No (fallback)",
        )

        return {"diagnosis": diagnosis, "llm_used": bool(llm_diagnosis)}, decision

    async def _reason_with_llm(
        self, alert: CloudWatchAlert, context: dict[str, Any]
    ):
        """Usa Bedrock (Nova o Claude) para analizar la alerta."""
        import boto3
        import json
        from src.config import settings
        from src.agents.decision_engine import Diagnosis, Severity

        service = alert.dimensions.get("ServiceName", "unknown")
        endpoint = alert.raw_payload.get("endpoint") or alert.namespace or "unknown"

        # Construir prompt para el LLM
        logs_context = ""
        if context.get("recent_logs"):
            logs_context = "\n".join([
                f"- {log.get('message', 'N/A')}" for log in context["recent_logs"][:5]
            ])

        prompt = f"""Eres un ingeniero SRE experto. Analiza esta alerta de un microservicio:

ALERTA:
- Servicio: {service}
- Endpoint: {endpoint}
- Tipo de error: {alert.raw_payload.get("error_type", "InternalServerError")}
- Código HTTP: {alert.raw_payload.get("status_code", 500)}
- Mensaje: {alert.reason}
- Duración: {alert.raw_payload.get("duration_ms", 0)}ms
- Trace ID: {alert.raw_payload.get("trace_id", "N/A")}

LOGS RECIENTES DE CLOUDWATCH:
{logs_context if logs_context else "No hay logs disponibles"}

Responde SOLAMENTE con un JSON válido con esta estructura:
{{
    "root_cause": "descripción de la causa raíz",
    "affected_component": "servicio/endpoint afectado",
    "error_category": "timeout|connection|auth|resource|unknown",
    "is_known": true/false,
    "confidence": 0.0-1.0,
    "severity": "CRITICA|ALTA|MEDIA|BAJA"
}}"""

        # Llamar a Bedrock
        bedrock_kwargs = {"region_name": settings.aws_region}
        if settings.aws_access_key_id:
            bedrock_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            bedrock_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            bedrock_kwargs["aws_session_token"] = settings.aws_session_token

        bedrock = boto3.client("bedrock-runtime", **bedrock_kwargs)

        model_id = settings.bedrock_model_id
        is_nova = model_id.startswith("amazon.") or model_id.startswith("us.amazon.")

        # El formato del request depende de la familia del modelo
        if is_nova:
            request_body = {
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {"maxTokens": 1024, "temperature": 0.1},
            }
        else:
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            }

        response = bedrock.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body),
        )

        # Parsear respuesta según la familia del modelo
        response_body = json.loads(response["body"].read())
        if is_nova:
            llm_response = response_body["output"]["message"]["content"][0]["text"]
        else:
            llm_response = response_body["content"][0]["text"]

        # Extraer JSON de la respuesta (permite objetos anidados)
        import re
        json_match = re.search(r"\{.*\}", llm_response, re.DOTALL)
        if json_match:
            diagnosis_data = json.loads(json_match.group())
            
            # Mapear severidad
            severity_map = {
                "CRITICA": Severity.CRITICA,
                "ALTA": Severity.ALTA,
                "MEDIA": Severity.MEDIA,
                "BAJA": Severity.BAJA,
            }
            
            return Diagnosis(
                root_cause=diagnosis_data.get("root_cause", alert.reason),
                affected_component=diagnosis_data.get("affected_component", f"{service}/unknown"),
                error_category=diagnosis_data.get("error_category", "unknown"),
                is_known=diagnosis_data.get("is_known", False),
                confidence=diagnosis_data.get("confidence", 0.5),
                severity=severity_map.get(diagnosis_data.get("severity", "MEDIA"), Severity.MEDIA),
            )
        
        return None

    async def _act(self, decision: RemediationDecision) -> list[RemediationAction]:
        """Fase de acción: ejecuta la remediación si es seguro."""
        actions_executed = []

        if decision.action == RemediationAction.SUGGEST:
            logger.info("Acción sugerida (no ejecutada): %s", decision.reason)
            return actions_executed

        if decision.action == RemediationAction.ESCALATE:
            logger.warning("Escalando a humano: %s", decision.reason)
            return actions_executed

        if decision.requires_confirmation:
            logger.info(
                "Requiere confirmación humana (confianza=%.2f): %s",
                decision.confidence,
                decision.reason,
            )
            return actions_executed

        # Ejecutar la skill
        try:
            if decision.skill_to_invoke:
                skill_result = await self._invoke_skill(
                    decision.skill_to_invoke, decision.skill_params
                )
                logger.info("Skill ejecutada: %s → %s", decision.skill_to_invoke, skill_result)
                actions_executed.append(decision.action)
        except Exception as e:
            logger.error("Error ejecutando skill %s: %s", decision.skill_to_invoke, str(e))

        return actions_executed

    async def _invoke_skill(self, skill_name: str, params: dict) -> str:
        """Invoca una skill del agente."""
        skill_map = {
            "restart_service": restart_service,
            "scale_up": scale_up,
            "clear_cache": clear_cache,
            "purge_queue": purge_queue,
        }

        skill = skill_map.get(skill_name)
        if not skill:
            raise ValueError(f"Skill desconocida: {skill_name}")

        # Ejecutar de forma asíncrona
        result = skill.invoke(params)
        return result

    async def _audit_trail(
        self,
        alert_id: str,
        alert: CloudWatchAlert,
        diagnosis: dict,
        decision: RemediationDecision,
        actions: list[RemediationAction],
    ):
        """Registra la acción en el audit trail."""
        diag = diagnosis.get("diagnosis")
        severity_value = diag.severity.value if hasattr(diag, "severity") else "UNKNOWN"
        
        audit_entry = {
            "alert_id": {"S": alert_id},
            "timestamp": {"S": datetime.utcnow().isoformat()},
            "alarm_name": {"S": alert.alarm_name},
            "service": {"S": alert.dimensions.get("ServiceName", "unknown")},
            "severity": {"S": severity_value},
            "action_taken": {"S": decision.action.value},
            "confidence": {"N": str(decision.confidence)},
            "actions_executed": {"S": str([a.value for a in actions])},
            "llm_used": {"S": str(diagnosis.get("llm_used", False))},
        }

        if not settings.enable_audit_trail:
            return

        try:
            aws_clients.dynamodb.put_item(
                TableName=settings.audit_table,
                Item=audit_entry,
            )
            logger.info("Audit trail registrado para alerta %s", alert_id)
        except aws_clients.dynamodb.exceptions.ResourceNotFoundException:
            # La tabla no existe (falta terraform apply). Se desactiva para no
            # repetir el error en cada alerta.
            logger.warning(
                "Tabla DynamoDB '%s' no existe. Audit trail desactivado. "
                "Ejecutar 'terraform apply' o poner KIRO_ENABLE_AUDIT_TRAIL=false.",
                settings.audit_table,
            )
            settings.enable_audit_trail = False
        except Exception as e:
            logger.warning("Error registrando audit trail: %s", str(e))

    def _build_analysis(
        self,
        diagnosis: dict,
        decision: RemediationDecision,
        actions: list[RemediationAction],
    ) -> str:
        """Construye el análisis completo para la respuesta."""
        diag = diagnosis.get("diagnosis")
        llm_used = diagnosis.get("llm_used", False)

        # Determinar fuente del análisis
        source = f"🧠 LLM (Bedrock: {settings.bedrock_model_id})" if llm_used else "⚙️ Motor de Reglas"

        analysis_parts = [
            f"## Diagnóstico del Agente SRE",
            f"",
            f"**Fuente del análisis**: {source}",
            f"**Severidad**: {diag.severity.value if diag else 'N/A'}",
            f"**Causa raíz**: {diag.root_cause if diag else 'N/A'}",
            f"**Servicio afectado**: {diag.affected_component if diag else 'N/A'}",
            f"**Categoría de error**: {diag.error_category if diag else 'N/A'}",
            f"**Error conocido**: {'Sí' if diag and diag.is_known else 'No'}",
            f"**Confianza**: {diag.confidence:.0%}" if diag else "**Confianza**: N/A",
            f"",
            f"## Acción Propuesta",
            f"",
            f"**Decisión**: {decision.action.value}",
            f"**Razón**: {decision.reason}",
            f"**Nivel de riesgo**: {decision.risk_level.value}",
            f"**Requiere confirmación**: {'Sí' if decision.requires_confirmation else 'No'}",
        ]

        if actions:
            analysis_parts.extend([
                f"",
                f"## Acciones Ejecutadas",
                f"",
            ])
            for action in actions:
                analysis_parts.append(f"- ✅ {action.value}")

        return "\n".join(analysis_parts)


def get_recent_incidents(limit: int = 10) -> list[dict]:
    """Devuelve los incidentes analizados más recientes (para el chat de Carmen)."""
    return list(INCIDENT_HISTORY)[:limit]


def get_incident_summary() -> dict:
    """Resumen agregado de los incidentes analizados en memoria."""
    incidents = list(INCIDENT_HISTORY)
    if not incidents:
        return {
            "total": 0,
            "services_affected": [],
            "by_error_type": {},
            "critical_count": 0,
            "latest": None,
        }

    by_error: dict[str, int] = {}
    services: set[str] = set()
    critical = 0
    for inc in incidents:
        by_error[inc["error_type"]] = by_error.get(inc["error_type"], 0) + 1
        services.add(inc["service"])
        if inc["severity"] in ("CRITICA", "ALTA"):
            critical += 1

    return {
        "total": len(incidents),
        "services_affected": sorted(services),
        "by_error_type": by_error,
        "critical_count": critical,
        "latest": incidents[0],
    }


# Singleton instance
orchestrator = Orchestrator()
