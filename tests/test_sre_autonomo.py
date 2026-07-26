"""Tests para el Agente SRE Autónomo."""

from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from src.agents.sre_autonomo.agent import _format_alert_message, analyze_alert
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


class TestFormatAlertMessage:
    """Tests para la función de formateo de alerta."""

    def test_includes_alarm_name(self):
        """El mensaje debe incluir el nombre de la alarma."""
        alert = _make_alert(alarm_name="my-test-alarm")
        message = _format_alert_message(alert)
        assert "my-test-alarm" in message

    def test_includes_state(self):
        """El mensaje debe incluir el estado."""
        alert = _make_alert(state="ALARM")
        message = _format_alert_message(alert)
        assert "ALARM" in message

    def test_includes_reason(self):
        """El mensaje debe incluir la razón."""
        alert = _make_alert(reason="CPU threshold crossed")
        message = _format_alert_message(alert)
        assert "CPU threshold crossed" in message

    def test_handles_none_optional_fields(self):
        """Debe manejar campos opcionales None sin errores."""
        alert = _make_alert(
            namespace=None,
            metric_name=None,
            previous_state=None,
        )
        message = _format_alert_message(alert)
        assert "N/A" in message


class TestAnalyzeAlert:
    """Tests para la función analyze_alert del agente."""

    @pytest.fixture
    def mock_agent(self):
        """Mock del agente para evitar llamadas a Bedrock."""
        fake_message = MagicMock()
        fake_message.content = "Severidad: ALTA. Causa raíz: memory leak."
        fake_message.name = None

        fake_tool_msg = MagicMock()
        fake_tool_msg.content = "Servicio escalado"
        fake_tool_msg.name = "scale_up"

        mock_result = {"messages": [fake_tool_msg, fake_message]}

        agent_mock = MagicMock()
        agent_mock.ainvoke = AsyncMock(return_value=mock_result)
        return agent_mock

    @pytest.mark.asyncio
    async def test_returns_webhook_response(self, mock_agent):
        """Debe retornar un WebhookResponse."""
        with patch("src.agents.sre_autonomo.agent._build_agent", return_value=mock_agent):
            alert = _make_alert()
            result = await analyze_alert(alert)
            assert isinstance(result, WebhookResponse)

    @pytest.mark.asyncio
    async def test_status_is_analyzed(self, mock_agent):
        """El status debe ser 'analyzed'."""
        with patch("src.agents.sre_autonomo.agent._build_agent", return_value=mock_agent):
            alert = _make_alert()
            result = await analyze_alert(alert)
            assert result.status == "analyzed"

    @pytest.mark.asyncio
    async def test_alert_id_is_generated(self, mock_agent):
        """Debe generar un alert_id único."""
        with patch("src.agents.sre_autonomo.agent._build_agent", return_value=mock_agent):
            alert = _make_alert()
            result = await analyze_alert(alert)
            assert result.alert_id is not None
            assert len(result.alert_id) > 0

    @pytest.mark.asyncio
    async def test_analysis_contains_agent_response(self, mock_agent):
        """El análisis debe contener la respuesta del agente."""
        with patch("src.agents.sre_autonomo.agent._build_agent", return_value=mock_agent):
            alert = _make_alert()
            result = await analyze_alert(alert)
            assert "Severidad: ALTA" in result.analysis

    @pytest.mark.asyncio
    async def test_actions_suggested_from_tools(self, mock_agent):
        """Las acciones sugeridas deben venir de las tools ejecutadas."""
        with patch("src.agents.sre_autonomo.agent._build_agent", return_value=mock_agent):
            alert = _make_alert()
            result = await analyze_alert(alert)
            assert "scale_up" in result.actions_suggested

    @pytest.mark.asyncio
    async def test_different_alerts_get_different_ids(self, mock_agent):
        """Cada alerta debe recibir un ID diferente."""
        with patch("src.agents.sre_autonomo.agent._build_agent", return_value=mock_agent):
            alert = _make_alert()
            result1 = await analyze_alert(alert)
            result2 = await analyze_alert(alert)
            assert result1.alert_id != result2.alert_id

    @pytest.mark.asyncio
    async def test_handles_agent_error_gracefully(self):
        """Debe manejar errores del agente sin crashear."""
        agent_mock = MagicMock()
        agent_mock.ainvoke = AsyncMock(side_effect=Exception("Bedrock timeout"))

        with patch("src.agents.sre_autonomo.agent._build_agent", return_value=agent_mock):
            alert = _make_alert()
            result = await analyze_alert(alert)
            assert result.status == "analyzed"
            assert "Error durante el análisis" in result.analysis
            assert result.actions_suggested == []
