"""Tests para el Agente SRE Autónomo."""

from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from src.agents.sre_autonomo.agent import analyze_alert
from src.models.alerts import CloudWatchAlert, WebhookResponse


def _make_alert(**overrides) -> CloudWatchAlert:
    """Helper para crear alertas de test."""
    defaults = {
        "alarm_name": "high-cpu-user-svc",
        "state": "ALARM",
        "reason": "Threshold Crossed: CPU > 80%",
        "namespace": "AWS/ECS",
        "metric_name": "CPUUtilization",
        "dimensions": {"ServiceName": "user-svc"},
    }
    defaults.update(overrides)
    return CloudWatchAlert(**defaults)


class TestAnalyzeAlert:
    """Tests para la función analyze_alert del agente."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock del orquestador para evitar llamadas a Bedrock."""
        mock_response = WebhookResponse(
            status="analyzed",
            alert_id="test-alert-id",
            analysis="Severidad: ALTA. Causa raíz: memory leak.",
            actions_suggested=["scale_up"],
        )

        with patch(
            "src.agents.sre_autonomo.agent.orchestrator"
        ) as mock:
            mock.process_alert = AsyncMock(return_value=mock_response)
            yield mock

    @pytest.mark.asyncio
    async def test_returns_webhook_response(self, mock_orchestrator):
        """Debe retornar un WebhookResponse."""
        alert = _make_alert()
        result = await analyze_alert(alert)
        assert isinstance(result, WebhookResponse)

    @pytest.mark.asyncio
    async def test_status_is_analyzed(self, mock_orchestrator):
        """El status debe ser 'analyzed'."""
        alert = _make_alert()
        result = await analyze_alert(alert)
        assert result.status == "analyzed"

    @pytest.mark.asyncio
    async def test_analysis_contains_agent_response(self, mock_orchestrator):
        """El análisis debe contener la respuesta del agente."""
        alert = _make_alert()
        result = await analyze_alert(alert)
        assert "Severidad: ALTA" in result.analysis

    @pytest.mark.asyncio
    async def test_actions_suggested_from_tools(self, mock_orchestrator):
        """Las acciones sugeridas deben venir de las tools ejecutadas."""
        alert = _make_alert()
        result = await analyze_alert(alert)
        assert "scale_up" in result.actions_suggested

    @pytest.mark.asyncio
    async def test_handles_agent_error_gracefully(self):
        """Debe manejar errores del agente sin crashear."""
        with patch(
            "src.agents.sre_autonomo.agent.orchestrator"
        ) as mock:
            mock.process_alert = AsyncMock(
                side_effect=Exception("Bedrock timeout")
            )
            alert = _make_alert()
            result = await analyze_alert(alert)
            assert result.status == "error"
            assert "Error durante el análisis" in result.analysis
