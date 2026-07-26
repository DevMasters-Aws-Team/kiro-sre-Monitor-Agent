"""Tests para el Decision Engine."""

import pytest

from src.agents.decision_engine import (
    DecisionEngine,
    RemediationAction,
    RiskLevel,
    Severity,
    decision_engine,
)


class TestDecisionEngine:
    """Tests para el motor de decisiones."""

    def test_singleton_exists(self):
        """Debe existir una instancia singleton."""
        assert decision_engine is not None
        assert isinstance(decision_engine, DecisionEngine)

    def test_classify_severity_critical(self):
        """Un error 503 con DatabaseTimeoutError debe ser CRITICA."""
        severity = decision_engine.classify_severity(
            status_code=503,
            error_type="DatabaseTimeoutError",
            service="payment-service",
            duration_ms=5000,
        )
        assert severity == Severity.CRITICA

    def test_classify_severity_alta(self):
        """Un error 500 genérico debe ser ALTA."""
        severity = decision_engine.classify_severity(
            status_code=500,
            error_type="InternalServerError",
            service="order-service",
            duration_ms=2000,
        )
        assert severity == Severity.ALTA

    def test_classify_severity_media(self):
        """Una respuesta lenta debe ser MEDIA."""
        severity = decision_engine.classify_severity(
            status_code=200,
            error_type=None,
            service="user-service",
            duration_ms=4000,
        )
        assert severity == Severity.MEDIA

    def test_classify_severity_baja(self):
        """Una respuesta normal debe ser BAJA."""
        severity = decision_engine.classify_severity(
            status_code=200,
            error_type=None,
            service="user-service",
            duration_ms=100,
        )
        assert severity == Severity.BAJA

    def test_diagnose_known_error(self):
        """Debe diagnosticar errores conocidos correctamente."""
        diagnosis = decision_engine.diagnose(
            service="payment-service",
            endpoint="POST /api/v1/sales/pay",
            status_code=503,
            error_type="DatabaseTimeoutError",
            error_message="Connection timeout acquiring connection from pool",
            duration_ms=3500,
        )

        assert diagnosis.root_cause == "Connection timeout acquiring connection from pool"
        assert diagnosis.affected_component == "payment-service/POST /api/v1/sales/pay"
        assert diagnosis.error_category == "timeout"
        assert diagnosis.is_known is True
        assert diagnosis.confidence == 0.85
        assert diagnosis.severity == Severity.CRITICA

    def test_diagnose_unknown_error(self):
        """Debe manejar errores desconocidos."""
        diagnosis = decision_engine.diagnose(
            service="unknown-service",
            endpoint="GET /api/unknown",
            status_code=500,
            error_type="UnknownError",
            error_message="Something went wrong",
            duration_ms=1000,
        )

        assert diagnosis.is_known is False
        assert diagnosis.confidence == 0.5

    def test_decide_action_known_error_high_confidence(self):
        """Un error conocido con alta confianza pero riesgo medio debe pedir confirmación."""
        diagnosis = decision_engine.diagnose(
            service="payment-service",
            endpoint="POST /api/v1/sales/pay",
            status_code=503,
            error_type="DatabaseTimeoutError",
            error_message="Connection timeout",
            duration_ms=3500,
        )

        decision = decision_engine.decide_action(diagnosis, "DatabaseTimeoutError")

        assert decision.action == RemediationAction.RESTART_SERVICE
        assert decision.skill_to_invoke == "restart_service"
        # Confidence 0.85 with MEDIUM risk requires confirmation
        assert decision.requires_confirmation is True
        assert decision.confidence == 0.85

    def test_decide_action_unknown_error(self):
        """Un error desconocido debe sugerir intervención humana."""
        diagnosis = decision_engine.diagnose(
            service="unknown-service",
            endpoint="GET /api/unknown",
            status_code=500,
            error_type="UnknownError",
            error_message="Something went wrong",
            duration_ms=1000,
        )

        decision = decision_engine.decide_action(diagnosis, "UnknownError")

        assert decision.action == RemediationAction.SUGGEST
        assert decision.skill_to_invoke is None
        assert decision.requires_confirmation is False

    def test_build_skill_params_restart(self):
        """Debe construir parámetros correctos para restart_service."""
        params = decision_engine._build_skill_params(
            RemediationAction.RESTART_SERVICE, "payment-service"
        )
        assert params == {"service_name": "payment-service"}

    def test_build_skill_params_scale_up(self):
        """Debe construir parámetros correctos para scale_up."""
        params = decision_engine._build_skill_params(
            RemediationAction.SCALE_UP, "order-service"
        )
        assert params == {"service_name": "order-service", "desired_count": 3}

    def test_build_skill_params_purge_queue(self):
        """Debe construir parámetros correctos para purge_queue."""
        params = decision_engine._build_skill_params(
            RemediationAction.PURGE_QUEUE, "order-service"
        )
        assert params == {"queue_name": "order-svc-dlq"}
