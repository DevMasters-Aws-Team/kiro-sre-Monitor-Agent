# Convenciones de Commits y Guía de Desarrollo

## Idioma
- Todos los commits, comentarios en código y documentación deben estar en **español**.
- Los nombres de variables, funciones y clases se mantienen en inglés (convención del ecosistema Python/LangChain).

---

## Formato de Commits

Los mensajes de commit deben ser descriptivos y explicar **qué se hizo, por qué y cómo**.

### Estructura

```
<tipo>(<alcance>): <descripción corta en español>

<cuerpo explicativo>
- Detalle de cada cambio significativo
- Razón del cambio
- Impacto en el sistema

<ejemplo de uso si aplica>
```

### Tipos permitidos
- `feat` — Nueva funcionalidad
- `fix` — Corrección de bug
- `refactor` — Reestructuración sin cambio funcional
- `docs` — Documentación
- `test` — Tests nuevos o modificados
- `chore` — Tareas de mantenimiento (deps, config, CI)

### Alcances comunes
- `agent` — Agente SRE principal
- `llm` — Proveedor de modelos LLM
- `mcp` — Adaptador MCP
- `skills` — Herramientas/skills del agente
- `config` — Configuración
- `infra` — Terraform / infraestructura
- `test` — Tests

### Ejemplo de commit correcto

```
feat(mcp): agregar adaptador MCP modular para tools externas

Se implementó un adaptador que conecta a cualquier servidor MCP
(Model Context Protocol) y expone sus herramientas al agente SRE.

Cambios:
- Crear src/adapters/mcp_adapter.py (clase MCPAdapter)
- Crear src/adapters/mcp_config.py (carga mcp_servers.json)
- Integrar MCP tools en el agente (agent.py _build_agent ahora es async)
- Agregar langchain-mcp-adapters como dependencia

Configuración (mcp_servers.json):
{
  "mcpServers": {
    "mi-server": {
      "transport": "streamable_http",
      "url": "https://mi-server.com/mcp"
    }
  }
}

El agente combina automáticamente tools locales (skills/) + tools MCP.
Si no hay MCP configurado, funciona solo con tools locales sin impacto.
```

### Ejemplo de commit de fix

```
fix(agent): corregir import de InMemorySaver desde langgraph

El import estaba apuntando a langchain.checkpoint.memory (no existe).
La ubicación correcta es langgraph.checkpoint.memory.

Antes:  from langchain.checkpoint.memory import InMemorySaver
Ahora:  from langgraph.checkpoint.memory import InMemorySaver

También se corrigió el typo 'checkpointinter' → 'checkpointer'.
```

---

## Arquitectura del Agente SRE

### Diagrama de componentes

```
┌─────────────────────────────────────────────────────────┐
│                    Agente SRE Autónomo                    │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │ LLM      │    │ create_agent │    │ InMemorySaver │  │
│  │ Provider │───▶│ (LangChain)  │◀───│ (checkpointer)│  │
│  └──────────┘    └──────┬───────┘    └───────────────┘  │
│                          │                                │
│              ┌───────────┴───────────┐                   │
│              │      ALL TOOLS        │                   │
│              ├───────────┬───────────┤                   │
│              │           │           │                   │
│  ┌───────────▼──┐  ┌────▼─────┐  ┌─▼────────────────┐  │
│  │ Local Skills │  │ MCP Tools│  │ (futuras tools)   │  │
│  │ restart_svc  │  │ context7 │  │                   │  │
│  │ scale_up     │  │ github   │  │                   │  │
│  │ clear_cache  │  │ custom   │  │                   │  │
│  │ purge_queue  │  │ ...      │  │                   │  │
│  └──────────────┘  └──────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Flujo de ejecución

1. Llega una alerta (CloudWatch → webhook POST)
2. `analyze_alert()` construye el agente con `_build_agent()`
3. `_build_agent()` resuelve el modelo via `llm_provider.get_model()`
4. Se cargan MCP tools (si hay configuradas en `mcp_servers.json`)
5. Se combinan LOCAL_TOOLS + MCP tools
6. `create_agent()` arma el grafo con LangGraph
7. El agente analiza, decide y ejecuta tools de remediación
8. Se retorna el análisis + acciones ejecutadas

### Archivos clave

| Archivo | Responsabilidad |
|---------|----------------|
| `src/agents/sre_autonomo/agent.py` | Orquestador principal del agente |
| `src/agents/llm_provider.py` | Resolución multi-cloud del modelo LLM |
| `src/agents/sre_autonomo/prompts.py` | System prompt del agente SRE |
| `src/adapters/mcp_adapter.py` | Adaptador MCP (tools externas) |
| `src/adapters/mcp_config.py` | Carga config de servidores MCP |
| `src/skills/*.py` | Herramientas locales de remediación |
| `src/config.py` | Configuración centralizada (pydantic-settings) |
| `mcp_servers.json` | Definición de servidores MCP |

---

## Proveedor de Modelos (LLM Provider)

El sistema soporta cualquier proveedor de modelo via un solo campo `KIRO_MODEL_ID`.

### Formato: `provider:model_name`

| Provider | Ejemplo | Auth |
|----------|---------|------|
| `ollama` | `ollama:qwen3:8b` | Sin auth (local) |
| `openai` | `openai:gpt-4o` | `OPENAI_API_KEY` |
| `azure_openai` | `azure_openai:gpt-5.4-nano` | Azure AD (az login) o API key |
| `bedrock_converse` | `bedrock_converse:anthropic.claude-3-sonnet-20240229-v1:0` | AWS credentials |
| `google_genai` | `google_genai:gemini-2.0-flash` | `GOOGLE_API_KEY` |
| `google_vertexai` | `google_vertexai:gemini-2.0-flash` | `gcloud auth` |
| `anthropic` | `anthropic:claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |

### Azure OpenAI con Azure AD (sin API key)
Para Azure con Azure AD, el sistema usa `DefaultAzureCredential` automáticamente.
Solo necesitas estar autenticado con `az login` y configurar:

```env
KIRO_MODEL_ID=azure_openai:gpt-5.4-nano
KIRO_AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com/
KIRO_AZURE_DEPLOYMENT=gpt-5.4-nano
KIRO_AZURE_USE_AD=true
```

---

## Adaptador MCP

### Para agregar un nuevo servidor MCP
Solo edita `mcp_servers.json`:

```json
{
  "mcpServers": {
    "nombre-server": {
      "transport": "streamable_http",
      "url": "https://url-del-server/mcp"
    }
  }
}
```

### Transportes soportados
- `streamable_http` — Servidor HTTP remoto o local
- `stdio` — Subproceso local (stdin/stdout)

### Para deshabilitar temporalmente
```json
{
  "disabled": true
}
```

No se necesita tocar código. El agente detecta automáticamente los cambios.

---

## Reglas de Desarrollo

1. **Siempre correr tests antes de commitear**: `uv run python tests/test_agent_e2e.py`
2. **No hardcodear credenciales** — usar variables de entorno o Azure AD
3. **Un commit por feature/fix** — no mezclar cambios no relacionados
4. **Agregar `langchain-mcp-adapters`** si se trabaja con MCP tools
5. **El `.env` no se commitea** — solo `.env.example` como referencia
6. **Los tests deben poder correr con cualquier modelo** configurado
