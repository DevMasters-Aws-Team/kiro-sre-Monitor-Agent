# Testing Standards - Kiro SRE Monitor Agent

## Estructura de Tests

Cada endpoint o funcionalidad nueva DEBE tener su archivo de test correspondiente siguiendo esta convención:

```
tests/
├── conftest.py              ← Fixtures compartidos (client, mocks AWS, etc.)
├── test_health.py           ← Tests para routers/health.py
├── test_webhook.py          ← Tests para routers/webhook.py
├── test_orchestrator.py     ← Tests para agents/orchestrator.py
└── ...
```

La regla es: `tests/test_<nombre_modulo>.py` para cada archivo en `src/`.

## Convenciones

- Framework: **pytest** + **pytest-asyncio**
- Cliente HTTP: **httpx** con `ASGITransport` para tests async
- Mocks: **unittest.mock** (patch de servicios externos como boto3, Bedrock)
- Cada test debe ser independiente y no depender de estado externo

## Estructura de un archivo de test

```python
import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestNombreEndpoint:
    """Tests para el endpoint /ruta."""

    async def test_caso_exitoso(self, client: AsyncClient):
        """Debe retornar 200 con respuesta válida."""
        response = await client.post("/ruta", json={...})
        assert response.status_code == 200
        data = response.json()
        assert "campo_esperado" in data

    async def test_validacion_input_invalido(self, client: AsyncClient):
        """Debe retornar 422 cuando el input es inválido."""
        response = await client.post("/ruta", json={})
        assert response.status_code == 422

    async def test_caso_borde(self, client: AsyncClient):
        """Describe el caso borde específico."""
        ...
```

## Qué testear por cada endpoint

Para cada endpoint nuevo, crear tests que cubran:

1. **Happy path** — Request válido, respuesta esperada
2. **Validación de input** — Campos requeridos faltantes, tipos incorrectos
3. **Casos borde** — Payloads vacíos, valores límite, caracteres especiales
4. **Errores de servicios externos** — Simular fallos de AWS, Bedrock, DynamoDB con mocks
5. **Códigos de respuesta** — Verificar status codes correctos (200, 201, 400, 422, 500)

## Qué testear por cada funcionalidad de agente

Para funciones en `src/agents/`:

1. **Análisis correcto** — Dado un input conocido, verificar que el output es coherente
2. **Manejo de errores** — Qué pasa si el LLM no responde o retorna basura
3. **Clasificación** — Verificar que la severidad/categoría se asigna correctamente
4. **Acciones sugeridas** — Validar que las skills recomendadas son válidas

## Mocks obligatorios

Nunca hacer llamadas reales a servicios externos en tests. Mockear siempre:

```python
from unittest.mock import AsyncMock, patch


@patch("src.agents.orchestrator.bedrock_client")
async def test_con_mock_bedrock(mock_bedrock, client):
    mock_bedrock.invoke.return_value = AsyncMock(return_value="respuesta simulada")
    response = await client.post("/webhook", json={...})
    assert response.status_code == 200
```

## Ejecutar tests

```bash
uv run pytest                    # Todos los tests
uv run pytest tests/test_webhook.py  # Un archivo específico
uv run pytest -v                 # Verbose
uv run pytest --tb=short         # Traceback corto en errores
```

## Checklist antes de hacer merge

- [ ] Cada endpoint tiene su `test_<nombre>.py`
- [ ] Cada función de agente tiene tests unitarios
- [ ] Todos los servicios externos están mockeados
- [ ] Tests pasan con `uv run pytest`
- [ ] No hay tests que dependan de orden de ejecución
