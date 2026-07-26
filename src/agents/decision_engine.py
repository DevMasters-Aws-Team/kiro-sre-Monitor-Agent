"""Decision Engine - Clasificación de severidad y evaluación de confianza."""

import logging
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    """Clasificación de severidad de incidentes."""
    CRITICA = "CRITICA"
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class RiskLevel(str, Enum):
    """Nivel de riesgo de una acción de remediación."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RemediationAction(str, Enum):
    """Acciones de remediación disponibles."""
    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    CLEAR_CACHE = "clear_cache"
    PURGE_QUEUE = "purge_queue"
    ESCALATE = "escalate"
    SUGGEST = "suggest"


@dataclass
class Diagnosis:
    """Diagnóstico de un incidente."""
    root_cause: str
    affected_component: str
    error_category: str  # timeout, connection, auth, resource, unknown
    is_known: bool
    confidence: float  # 0.0 - 1.0
    severity: Severity


@dataclass
class RemediationDecision:
    """Decisión de remediación."""
    action: RemediationAction
    skill_to_invoke: str | None
    skill_params: dict
    risk_level: RiskLevel
    requires_confirmation: bool
    reason: str
    confidence: float


class DecisionEngine:
    """Motor de decisiones para el agente SRE."""

    # Error types and their typical remediation
    KNOWN_ERRORS = {
        "DatabaseTimeoutError": {
            "action": RemediationAction.RESTART_SERVICE,
            "risk_level": RiskLevel.MEDIUM,
            "confidence": 0.85,
        },
        "PaymentGatewayTimeoutError": {
            "action": RemediationAction.RESTART_SERVICE,
            "risk_level": RiskLevel.MEDIUM,
            "confidence": 0.80,
        },
        "BiometricServiceFailure": {
            "action": RemediationAction.CLEAR_CACHE,
            "risk_level": RiskLevel.LOW,
            "confidence": 0.75,
        },
        "InventoryLockError": {
            "action": RemediationAction.PURGE_QUEUE,
            "risk_level": RiskLevel.MEDIUM,
            "confidence": 0.70,
        },
        "InternalServerError": {
            "action": RemediationAction.RESTART_SERVICE,
            "risk_level": RiskLevel.MEDIUM,
            "confidence": 0.60,
        },
    }

    # Service to queue mapping for purge_queue
    SERVICE_QUEUE_MAP = {
        "order-service": "order-svc-dlq",
        "payment-service": "pay-svc-dlq",
        "inventory-service": "inventory-svc-dlq",
    }

    def classify_severity(
        self,
        status_code: int,
        error_type: str | None,
        service: str,
        duration_ms: float,
    ) -> Severity:
        """Clasifica la severidad de un incidente."""
        # Critical: 5xx errors with specific types
        if status_code >= 500:
            if error_type in ("DatabaseTimeoutError", "PaymentGatewayTimeoutError"):
                return Severity.CRITICA
            return Severity.ALTA

        # High: 4xx errors that indicate system issues
        if status_code >= 400:
            if error_type == "BiometricServiceFailure":
                return Severity.ALTA
            return Severity.MEDIA

        # Medium: Slow responses
        if duration_ms > 3000:
            return Severity.MEDIA

        return Severity.BAJA

    def diagnose(
        self,
        service: str,
        endpoint: str,
        status_code: int,
        error_type: str | None,
        error_message: str,
        duration_ms: float,
    ) -> Diagnosis:
        """Realiza un diagnóstico del incidente."""
        severity = self.classify_severity(
            status_code, error_type, service, duration_ms
        )

        # Determine error category
        if error_type and "Timeout" in error_type:
            error_category = "timeout"
        elif error_type and ("Connection" in error_type or "Lock" in error_type):
            error_category = "connection"
        elif status_code == 401:
            error_category = "auth"
        elif error_type and "Resource" in error_type:
            error_category = "resource"
        else:
            error_category = "unknown"

        # Check if known error
        is_known = error_type in self.KNOWN_ERRORS if error_type else False
        confidence = self.KNOWN_ERRORS.get(error_type, {}).get("confidence", 0.5) if error_type else 0.5

        return Diagnosis(
            root_cause=error_message or f"Error {status_code} en {service}",
            affected_component=f"{service}/{endpoint}",
            error_category=error_category,
            is_known=is_known,
            confidence=confidence,
            severity=severity,
        )

    def decide_action(
        self,
        diagnosis: Diagnosis,
        error_type: str | None,
    ) -> RemediationDecision:
        """Decide qué acción de remediación tomar."""
        if not diagnosis.is_known or not error_type:
            return RemediationDecision(
                action=RemediationAction.SUGGEST,
                skill_to_invoke=None,
                skill_params={},
                risk_level=RiskLevel.LOW,
                requires_confirmation=False,
                reason="Error desconocido. Se requiere intervención humana.",
                confidence=diagnosis.confidence,
            )

        known_error = self.KNOWN_ERRORS[error_type]
        action = known_error["action"]
        risk_level = known_error["risk_level"]

        # Determine if auto-execution is allowed
        auto_execute = (
            diagnosis.confidence >= 0.9
            or (diagnosis.confidence >= 0.7 and risk_level == RiskLevel.LOW)
        )

        # Build skill params
        service = diagnosis.affected_component.split("/")[0]
        skill_params = self._build_skill_params(action, service)

        return RemediationDecision(
            action=action,
            skill_to_invoke=action.value if action != RemediationAction.ESCALATE else None,
            skill_params=skill_params,
            risk_level=risk_level,
            requires_confirmation=not auto_execute,
            reason=f"Error conocido: {error_type}. Confianza: {diagnosis.confidence:.0%}",
            confidence=diagnosis.confidence,
        )

    def _build_skill_params(self, action: RemediationAction, service: str) -> dict:
        """Construye los parámetros para la skill."""
        if action == RemediationAction.RESTART_SERVICE:
            return {"service_name": service}
        elif action == RemediationAction.SCALE_UP:
            return {"service_name": service, "desired_count": 3}
        elif action == RemediationAction.CLEAR_CACHE:
            return {"service_name": service}
        elif action == RemediationAction.PURGE_QUEUE:
            queue_name = self.SERVICE_QUEUE_MAP.get(service, f"{service}-dlq")
            return {"queue_name": queue_name}
        return {}


# Singleton instance
decision_engine = DecisionEngine()
