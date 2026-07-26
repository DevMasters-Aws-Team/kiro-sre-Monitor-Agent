"""Carga y validación de configuración de servidores MCP.

Lee la configuración de MCP servers desde un archivo JSON,
soportando múltiples servidores con diferentes transportes.

Formato del archivo de configuración (mcp_servers.json):
{
    "mcpServers": {
        "server-name": {
            "transport": "streamable_http" | "stdio",
            "url": "https://...",              // para streamable_http
            "headers": {"key": "value"},       // opcional, para streamable_http
            "command": "python",               // para stdio
            "args": ["server.py"],             // para stdio
            "env": {"KEY": "VALUE"},           // opcional, para stdio
            "disabled": false                  // opcional, desactiva el server
        }
    }
}
"""

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Path por defecto del archivo de configuración
DEFAULT_CONFIG_PATH = Path("mcp_servers.json")


class MCPServerConfig(BaseModel):
    """Configuración de un servidor MCP individual."""

    transport: str = Field(..., description="Tipo de transporte: streamable_http o stdio")
    url: str | None = Field(None, description="URL del servidor (para streamable_http)")
    headers: dict[str, str] = Field(default_factory=dict, description="Headers HTTP opcionales")
    command: str | None = Field(None, description="Comando a ejecutar (para stdio)")
    args: list[str] = Field(default_factory=list, description="Argumentos del comando (para stdio)")
    env: dict[str, str] = Field(default_factory=dict, description="Variables de entorno (para stdio)")
    disabled: bool = Field(False, description="Si está desactivado, no se conecta")

    def to_client_config(self) -> dict[str, Any]:
        """Convierte a formato compatible con MultiServerMCPClient."""
        config: dict[str, Any] = {"transport": self.transport}

        if self.transport == "streamable_http":
            if not self.url:
                raise ValueError("'url' es requerido para transporte streamable_http")
            config["url"] = self.url
            if self.headers:
                config["headers"] = self.headers

        elif self.transport == "stdio":
            if not self.command:
                raise ValueError("'command' es requerido para transporte stdio")
            config["command"] = self.command
            if self.args:
                config["args"] = self.args
            if self.env:
                config["env"] = self.env

        else:
            raise ValueError(f"Transporte no soportado: {self.transport}")

        return config


class MCPConfig(BaseModel):
    """Configuración completa de servidores MCP."""

    servers: dict[str, MCPServerConfig] = Field(
        default_factory=dict,
        description="Mapa de nombre -> configuración de cada servidor MCP",
    )

    def get_active_servers(self) -> dict[str, MCPServerConfig]:
        """Retorna solo los servidores que no están desactivados."""
        return {name: cfg for name, cfg in self.servers.items() if not cfg.disabled}

    def to_client_config(self) -> dict[str, dict[str, Any]]:
        """Convierte a formato compatible con MultiServerMCPClient."""
        return {
            name: cfg.to_client_config()
            for name, cfg in self.get_active_servers().items()
        }


def load_mcp_config(config_path: Path | str | None = None) -> MCPConfig:
    """Carga la configuración de MCP servers desde un archivo JSON.

    Args:
        config_path: Ruta al archivo de configuración. Si es None, busca
                     mcp_servers.json en el directorio del proyecto.

    Returns:
        MCPConfig con la configuración parseada.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    path = Path(config_path)

    if not path.exists():
        logger.info("No se encontró archivo MCP config en: %s (sin MCP servers)", path)
        return MCPConfig(servers={})

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.error("Error parseando MCP config %s: %s", path, e)
        return MCPConfig(servers={})

    # Soportar formato {"mcpServers": {...}} o directamente {server: config}
    if "mcpServers" in raw:
        servers_raw = raw["mcpServers"]
    else:
        servers_raw = raw

    servers = {}
    for name, cfg in servers_raw.items():
        try:
            servers[name] = MCPServerConfig(**cfg)
        except Exception as e:
            logger.warning("Error parseando servidor MCP '%s': %s (ignorando)", name, e)

    config = MCPConfig(servers=servers)
    active = config.get_active_servers()
    logger.info(
        "MCP config cargada: %d servidores (%d activos)",
        len(config.servers),
        len(active),
    )

    return config
