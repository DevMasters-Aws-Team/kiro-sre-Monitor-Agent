"""Tests para el Event Handler."""

import pytest
from unittest.mock import AsyncMock, patch

from src.agents.event_handler import EventBridgeHandler, event_handler


class TestEventBridgeHandler:
    """Tests para el handler de EventBridge."""

    def test_singleton_exists(self):
        """Debe existir una instancia singleton."""
        assert event_handler is not None
        assert isinstance(event_handler, EventBridgeHandler)

    @pytest.mark.asyncio
    async def test_handle_cloudwatch_alarm(self):
        """Debe manejar eventos de CloudWatch Alarm."""
        event = {
            "source": "aws.cloudwatch",
            "detail-type": "CloudWatch Alarm State Change",
            "detail": {
                "alarmName": "kiro-high-cpu",
                "state": {
                    "value": "ALARM",
                    "reason": "Threshold Crossed",
                },
                "namespace": "AWS/ECS",
                "dimensions": {"ServiceName": "payment-service"},
            },
        }

        with patch.object(
            event_handler.orchestrator,
            "process_alert",
            new_callable=AsyncMock,
        ) as mock_process:
            mock_process.return_value = AsyncMock(
                alert_id="test-id",
                analysis="Test analysis",
            )

            result = await event_handler.handle_event(event)

            assert result["status"] == "processed"
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_ecs_task_change(self):
        """Debe manejar eventos de cambio de tarea ECS."""
        event = {
            "source": "aws.ecs",
            "detail-type": "ECS Task State Change",
            "detail": {
                "taskArn": "arn:aws:ecs:us-east-1:123456789:task/cluster/task-id",
                "clusterArn": "arn:aws:ecs:us-east-1:123456789:cluster/kiro-cluster",
                "lastStatus": "STOPPED",
                "stoppedReason": "Essential container exited",
            },
        }

        with patch.object(
            event_handler.orchestrator,
            "process_alert",
            new_callable=AsyncMock,
        ) as mock_process:
            mock_process.return_value = AsyncMock(
                alert_id="test-id",
                analysis="Test analysis",
            )

            result = await event_handler.handle_event(event)

            assert result["status"] == "processed"
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_application_error(self):
        """Debe manejar eventos de error de aplicación."""
        event = {
            "source": "kiro.microservices",
            "detail-type": "ApplicationError",
            "detail": {
                "service": "payment-service",
                "errorType": "DatabaseTimeoutError",
                "message": "Connection timeout",
                "statusCode": 503,
            },
        }

        with patch.object(
            event_handler.orchestrator,
            "process_alert",
            new_callable=AsyncMock,
        ) as mock_process:
            mock_process.return_value = AsyncMock(
                alert_id="test-id",
                analysis="Test analysis",
            )

            result = await event_handler.handle_event(event)

            assert result["status"] == "processed"
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_unknown_event(self):
        """Debe ignorar eventos desconocidos."""
        event = {
            "source": "unknown.source",
            "detail-type": "UnknownEvent",
            "detail": {},
        }

        result = await event_handler.handle_event(event)

        assert result["status"] == "ignored"
