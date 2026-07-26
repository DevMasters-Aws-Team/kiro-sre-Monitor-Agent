"""Adaptador MCP modular para el Agente SRE.

Conecta a cualquier servidor MCP (stdio o HTTP) y expone sus tools
como herramientas compatibles con LangChain/LangGraph.

Uso:
    adapter = MCPAdapter()
    tools = await adapter.get_tools()
    # Pasar tools al agente junto con las skills locales

    # Al finalizar (opcional para stateless):
    await adapter.close()
"""

import logging
from pathlib import Path
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.adapters.mcp_config import MCPConfig, load_mcp_config

logger = logging.getLogger(__name__)


class MCPAdapter:
    """Adaptador que conecta a servidores MCP y expone sus tools para LangChain.

    Soporta:
      - Múltiples servidores MCP simultáneos
      - Transportes: streamable_http (HTTP/SSE) y stdio (subproceso)
      - Configuración via archivo JSON (mcp_servers.json)
      - Configuración programática (dict)
      - Hot-reload de configuración

    Ejemplo con archivo de config:
        adapter = MCPAdapter()  # lee mcp_servers.json
        tools = await adapter.get_tools()

    Ejemplo programático:
        adapter = MCPAdapter.from_dict({
            "my-server": {
                "transport": "streamable_http",
                "url": "https://my-mcp-server.com/mcp"
            }
        })
        tools = await adapter.get_tools()
    """

    def __init__(
        self,
        config_path: Path | str | None = None,
        config: MCPConfig | None = None,
    ):
        """Inicializa el adaptador MCP.

        Args:
            config_path: Ruta al archivo mcp_servers.json.
                         Si es None, busca en el directorio actual.
            config: Configuración directa (tiene prioridad sobre config_path).
        """
        if config is not None:
            self._config = config
        else:
            self._config = load_mcp_config(config_path)

        self._client: MultiServerMCPClient | None = None
        self._tools: list[BaseTool] = []

    @classmethod
    def from_dict(cls, servers: dict[str, dict[str, Any]]) -> "MCPAdapter":
        """Crea un adaptador desde un diccionario de configuración.

        Args:
            servers: Dict con formato {nombre: {transport, url/command, ...}}

        Returns:
            MCPAdapter configurado.

        Ejemplo:
            adapter = MCPAdapter.from_dict({
                "docs": {
                    "transport": "streamable_http",
                    "url": "https://docs.example.com/mcp"
                },
                "calculator": {
                    "transport": "stdio",
                    "command": "python",
                    "args": ["calc_server.py"]
                }
            })
        """
        from src.adapters.mcp_config import MCPServerConfig

        parsed_servers = {}
        for name, cfg in servers.items():
            parsed_servers[name] = MCPServerConfig(**cfg)

        config = MCPConfig(servers=parsed_servers)
        return cls(config=config)

    @property
    def is_configured(self) -> bool:
        """Indica si hay al menos un servidor MCP configurado y activo."""
        return len(self._config.get_active_servers()) > 0

    @property
    def server_names(self) -> list[str]:
        """Nombres de los servidores MCP activos."""
        return list(self._config.get_active_servers().keys())

    async def get_tools(self) -> list[BaseTool]:
        """Obtiene todas las herramientas de los servidores MCP configurados.

        Conecta a todos los servidores activos y retorna sus tools
        como objetos BaseTool de LangChain.

        Returns:
            Lista de tools de todos los servidores MCP.
            Lista vacía si no hay servidores configurados.
        """
        if not self.is_configured:
            logger.debug("No hay servidores MCP configurados, retornando lista vacía")
            return []

        client_config = self._config.to_client_config()

        logger.info(
            "Conectando a %d servidor(es) MCP: %s",
            len(client_config),
            list(client_config.keys()),
        )

        try:
            self._client = MultiServerMCPClient(client_config)
            self._tools = await self._client.get_tools()

            logger.info(
                "MCP tools cargadas: %d herramientas de %d servidor(es)",
                len(self._tools),
                len(client_config),
            )

            for tool in self._tools:
                logger.debug("  → %s: %s", tool.name, tool.description[:80] if tool.description else "")

            return self._tools

        except Exception as e:
            logger.error("Error conectando a servidores MCP: %s", e)
            return []

    async def reload(self, config_path: Path | str | None = None) -> list[BaseTool]:
        """Recarga la configuración y reconecta a los servidores MCP.

        Útil para hot-reload cuando se modifica mcp_servers.json.

        Args:
            config_path: Nueva ruta de configuración (opcional).

        Returns:
            Lista actualizada de tools.
        """
        await self.close()
        self._config = load_mcp_config(config_path)
        return await self.get_tools()

    async def close(self):
        """Cierra las conexiones a los servidores MCP."""
        self._client = None
        self._tools = []
        logger.debug("Conexiones MCP cerradas")

    def __repr__(self) -> str:
        active = self._config.get_active_servers()
        return (
            f"MCPAdapter(servers={list(active.keys())}, "
            f"tools_loaded={len(self._tools)})"
        )
