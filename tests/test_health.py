"""Tests para el endpoint /health."""

import pytest
from httpx import AsyncClient


class TestHealth:
    """Tests para el endpoint GET /health."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client: AsyncClient):
        """Debe retornar 200 con status ok."""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_response_body(self, client: AsyncClient):
        """Debe retornar status ok y el environment actual."""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        assert "environment" in data

    @pytest.mark.asyncio
    async def test_health_environment_is_dev(self, client: AsyncClient):
        """En tests debe reportar environment dev."""
        response = await client.get("/health")
        data = response.json()
        assert data["environment"] == "dev"
