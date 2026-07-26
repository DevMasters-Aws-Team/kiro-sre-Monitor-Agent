"""Tests para el Orchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.orchestrator import Orchestrator, orchestrator
from src.models.alerts import CloudWatchAlert, WebhookResponse


class TestOrchestrator:
    """Tests para el orquestador principal."""

    def test_singleton_exists(self):
        """Debe existir una instancia singleton."""
        assert orchestrator is not None
        assert isinstance(orchestrator, Orchestrator)

    def _make_alert(self, **overrides) -> CloudWatchAlert:
        """Helper para crear alertas de test."""
        defaults = {
            "alarm_name": "test-high-cpu",
            "state": "ALARM",
            "reason": "CPU threshold crossed",
            "namespace": "AWS/ECS",
            "metric_name": "CPUUtilization",
            "dimensions": {"ServiceName": "payment-service"},
            "raw_payload": {
                "error_type": "DatabaseTimeoutError",
                "status_code": 503,
                "duration_ms": 3500,
            },
        }
        defaults.update(overrides)
        return CloudWatchAlert(**defaults)

    @pytest.mark.asyncio
    async def test_process_alert_returns_webhook_response(self):
        """Debe retornar un WebhookResponse."""
        alert = self._make_alert()

        with patch.object(
            orchestrator,
            "_observe",
            new_callable=AsyncMock,
        ) as mock_observe:
            mock_observe.return_value = {"recent_logs": []}

            with patch.object(
                orchestrator,
                "_reason",
                new_callable=AsyncMock,
            ) as mock_reason:
                mock_diagnosis = MagicMock()
                mock_diagnosis.severity.value = "CRITICA"
                mock_diagnosis.root_cause = "Connection timeout"
                mock_diagnosis.affected_component = "payment-service/POST /api/v1/sales/pay"
                mock_diagnosis.error_category = "timeout"
                mock_diagnosis.is_known = True
                mock_diagnosis.confidence = 0.85

                mock_decision = MagicMock()
                mock_decision.action.value = "restart_service"
                mock_decision.skill_to_invoke = "restart_service"
                mock_decision.confidence = 0.85
                mock_decision.requires_confirmation = False
                mock_decision.reason = "Error conocido"
                mock_decision.risk_level.value = "medium"

                mock_reason.return_value = (
                    {"diagnosis": mock_diagnosis},
                    mock_decision,
                )

                with patch.object(
                    orchestrator,
                    "_act",
                    new_callable=AsyncMock,
                ) as mock_act:
                    mock_act.return_value = []

                    with patch.object(
                        orchestrator,
                        "_audit_trail",
                        new_callable=AsyncMock,
                    ):
                        result = await orchestrator.process_alert(alert)

                        assert isinstance(result, WebhookResponse)
                        assert result.status == "analyzed"
                        assert result.alert_id is not None

    @pytest.mark.asyncio
    async def test_observe_returns_context(self):
        """_observe debe retornar contexto de la alerta."""
        alert = self._make_alert()

        context = await orchestrator._observe(alert)

        assert "alert" in context
        assert "recent_logs" in context
        assert context["alert"] == alert

    @pytest.mark.asyncio
    async def test_reason_returns_diagnosis_and_decision(self):
        """_reason debe retornar diagnóstico y decisión."""
        alert = self._make_alert()
        context = {"recent_logs": []}

        diagnosis_dict, decision = await orchestrator._reason(alert, context)

        assert "diagnosis" in diagnosis_dict
        assert decision is not None
        assert hasattr(decision, "action")
        assert hasattr(decision, "confidence")
