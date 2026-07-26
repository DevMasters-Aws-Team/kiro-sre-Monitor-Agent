"""Tests para el endpoint POST /webhook."""

from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from src.models.alerts import WebhookResponse


VALID_ALERT_PAYLOAD = {
    "alarm_name": "high-cpu-user-svc",
    "state": "ALARM",
    "reason": "Threshold Crossed: CPU > 80%",
    "namespace": "AWS/ECS",
    "metric_name": "CPUUtilization",
    "dimensions": {"ServiceName": "user-svc"},
}


@pytest.fixture(autouse=True)
def mock_agent():
    """Mock del agente para todos los tests del webhook (evita llamadas a Bedrock)."""
    fake_message = MagicMock()
    fake_message.content = "Severidad: ALTA. Escalar servicio recomendado."
    fake_message.name = None

    mock_result = {"messages": [fake_message]}

    agent_mock = MagicMock()
    agent_mock.ainvoke = AsyncMock(return_value=mock_result)

    with patch("src.agents.sre_autonomo.agent._build_agent", return_value=agent_mock):
        yield


class TestWebhook:
    """Tests para el endpoint POST /webhook."""

    @pytest.mark.asyncio
    async def test_webhook_returns_200_with_valid_payload(self, client: AsyncClient):
        """Debe retornar 200 con un payload válido."""
        response = await client.post("/webhook", json=VALID_ALERT_PAYLOAD)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_response_has_required_fields(self, client: AsyncClient):
        """La respuesta debe contener status, alert_id, analysis y actions_suggested."""
        response = await client.post("/webhook", json=VALID_ALERT_PAYLOAD)
        data = response.json()
        assert "status" in data
        assert "alert_id" in data
        assert "analysis" in data
        assert "actions_suggested" in data

    @pytest.mark.asyncio
    async def test_webhook_status_is_analyzed(self, client: AsyncClient):
        """El status de la respuesta debe ser 'analyzed'."""
        response = await client.post("/webhook", json=VALID_ALERT_PAYLOAD)
        data = response.json()
        assert data["status"] == "analyzed"

    @pytest.mark.asyncio
    async def test_webhook_alert_id_is_uuid(self, client: AsyncClient):
        """El alert_id debe ser un UUID válido."""
        import uuid

        response = await client.post("/webhook", json=VALID_ALERT_PAYLOAD)
        data = response.json()
        uuid.UUID(data["alert_id"])  # raises ValueError si no es UUID válido

    @pytest.mark.asyncio
    async def test_webhook_analysis_not_empty(self, client: AsyncClient):
        """El análisis no debe estar vacío."""
        response = await client.post("/webhook", json=VALID_ALERT_PAYLOAD)
        data = response.json()
        assert data["analysis"] is not None
        assert len(data["analysis"]) > 0

    @pytest.mark.asyncio
    async def test_webhook_missing_alarm_name_returns_422(self, client: AsyncClient):
        """Debe retornar 422 si falta alarm_name."""
        payload = {"state": "ALARM", "reason": "test"}
        response = await client.post("/webhook", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_webhook_missing_state_returns_422(self, client: AsyncClient):
        """Debe retornar 422 si falta state."""
        payload = {"alarm_name": "test", "reason": "test"}
        response = await client.post("/webhook", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_webhook_missing_reason_returns_422(self, client: AsyncClient):
        """Debe retornar 422 si falta reason."""
        payload = {"alarm_name": "test", "state": "ALARM"}
        response = await client.post("/webhook", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_webhook_empty_body_returns_422(self, client: AsyncClient):
        """Debe retornar 422 con body vacío."""
        response = await client.post("/webhook", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_webhook_minimal_payload(self, client: AsyncClient):
        """Debe funcionar con solo los campos requeridos."""
        minimal = {
            "alarm_name": "test-alarm",
            "state": "OK",
            "reason": "Threshold OK",
        }
        response = await client.post("/webhook", json=minimal)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_with_all_optional_fields(self, client: AsyncClient):
        """Debe funcionar con todos los campos opcionales incluidos."""
        full_payload = {
            "alarm_name": "high-latency-pay-svc",
            "alarm_description": "Latencia alta en servicio de pagos",
            "state": "ALARM",
            "previous_state": "OK",
            "reason": "Threshold Crossed: p99 > 2000ms",
            "region": "us-east-1",
            "namespace": "AWS/ECS",
            "metric_name": "ResponseTime",
            "dimensions": {"ServiceName": "pay-svc", "ClusterName": "kiro-cluster"},
            "raw_payload": {"source": "cloudwatch", "detail-type": "CloudWatch Alarm"},
        }
        response = await client.post("/webhook", json=full_payload)
        assert response.status_code == 200
