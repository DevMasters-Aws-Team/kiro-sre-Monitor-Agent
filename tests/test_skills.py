"""Tests para las skills (tools) del agente."""

import pytest

from src.skills.restart_service import restart_service
from src.skills.scale_up import scale_up
from src.skills.clear_cache import clear_cache
from src.skills.purge_queue import purge_queue


class TestRestartService:
    """Tests para la skill restart_service."""

    def test_returns_string(self):
        """Debe retornar un string con el resultado."""
        result = restart_service.invoke({"service_name": "user-svc"})
        assert isinstance(result, str)

    def test_includes_service_name_in_response(self):
        """La respuesta debe mencionar el servicio reiniciado."""
        result = restart_service.invoke({"service_name": "order-svc"})
        assert "order-svc" in result

    def test_tool_name(self):
        """El nombre de la tool debe ser restart_service."""
        assert restart_service.name == "restart_service"

    def test_tool_has_description(self):
        """La tool debe tener una descripción."""
        assert restart_service.description is not None
        assert len(restart_service.description) > 0


class TestScaleUp:
    """Tests para la skill scale_up."""

    def test_returns_string(self):
        """Debe retornar un string con el resultado."""
        result = scale_up.invoke({"service_name": "user-svc", "desired_count": 5})
        assert isinstance(result, str)

    def test_includes_service_name(self):
        """La respuesta debe mencionar el servicio escalado."""
        result = scale_up.invoke({"service_name": "pay-svc", "desired_count": 3})
        assert "pay-svc" in result

    def test_includes_desired_count(self):
        """La respuesta debe mencionar el número de tareas."""
        result = scale_up.invoke({"service_name": "pay-svc", "desired_count": 4})
        assert "4" in result

    def test_tool_name(self):
        """El nombre de la tool debe ser scale_up."""
        assert scale_up.name == "scale_up"


class TestClearCache:
    """Tests para la skill clear_cache."""

    def test_returns_string(self):
        """Debe retornar un string con el resultado."""
        result = clear_cache.invoke({"service_name": "auth-svc"})
        assert isinstance(result, str)

    def test_includes_service_name(self):
        """La respuesta debe mencionar el servicio."""
        result = clear_cache.invoke({"service_name": "auth-svc"})
        assert "auth-svc" in result

    def test_tool_name(self):
        """El nombre de la tool debe ser clear_cache."""
        assert clear_cache.name == "clear_cache"


class TestPurgeQueue:
    """Tests para la skill purge_queue."""

    def test_returns_string(self):
        """Debe retornar un string con el resultado."""
        result = purge_queue.invoke({"queue_name": "order-svc-dlq"})
        assert isinstance(result, str)

    def test_includes_queue_name(self):
        """La respuesta debe mencionar la cola purgada."""
        result = purge_queue.invoke({"queue_name": "pay-svc-queue"})
        assert "pay-svc-queue" in result

    def test_tool_name(self):
        """El nombre de la tool debe ser purge_queue."""
        assert purge_queue.name == "purge_queue"
