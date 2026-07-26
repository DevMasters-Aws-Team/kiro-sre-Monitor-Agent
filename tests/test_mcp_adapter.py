"""Test del adaptador MCP - verifica conectividad con servidores MCP."""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.adapters.mcp_adapter import MCPAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_mcp_from_config_file():
    """Test: cargar MCP tools desde mcp_servers.json."""
    print("\n" + "=" * 70)
    print("TEST MCP: Cargar tools desde mcp_servers.json")
    print("=" * 70)

    adapter = MCPAdapter()

    if not adapter.is_configured:
        print("⚠ No hay servidores MCP configurados (mcp_servers.json)")
        print("  → Crea mcp_servers.json con al menos un servidor activo")
        return False

    print(f"✓ Servidores configurados: {adapter.server_names}")

    tools = await adapter.get_tools()

    if not tools:
        print("⚠ No se obtuvieron tools (servidor puede estar caído)")
        return False

    print(f"✓ Tools obtenidas: {len(tools)}")
    for tool in tools:
        desc = tool.description[:60] if tool.description else "sin descripción"
        print(f"  → {tool.name}: {desc}")

    print("\n✓ TEST PASADO - MCP adapter funciona correctamente")
    return True


async def test_mcp_programmatic():
    """Test: crear MCP adapter programáticamente."""
    print("\n" + "=" * 70)
    print("TEST MCP: Crear adapter programáticamente")
    print("=" * 70)

    adapter = MCPAdapter.from_dict({
        "context7": {
            "transport": "streamable_http",
            "url": "https://mcp.context7.com/mcp",
        }
    })

    print(f"✓ Adapter creado: {adapter}")
    print(f"✓ Servidores: {adapter.server_names}")

    tools = await adapter.get_tools()

    if tools:
        print(f"✓ Tools cargadas: {len(tools)}")
        print("\n✓ TEST PASADO")
        return True
    else:
        print("⚠ No se obtuvieron tools")
        return False


async def test_mcp_disabled_server():
    """Test: servidor deshabilitado no conecta."""
    print("\n" + "=" * 70)
    print("TEST MCP: Servidor deshabilitado")
    print("=" * 70)

    adapter = MCPAdapter.from_dict({
        "disabled-server": {
            "transport": "streamable_http",
            "url": "https://mcp.context7.com/mcp",
            "disabled": True,
        }
    })

    if not adapter.is_configured:
        print("✓ Servidor deshabilitado no se reporta como configurado")
        tools = await adapter.get_tools()
        if len(tools) == 0:
            print("✓ No retorna tools (correcto)")
            print("\n✓ TEST PASADO")
            return True

    print("✗ ERROR - servidor deshabilitado no debería estar activo")
    return False


async def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║            TEST SUITE - MCP Adapter                                ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    results = {}
    results["disabled"] = await test_mcp_disabled_server()
    results["programmatic"] = await test_mcp_programmatic()
    results["config_file"] = await test_mcp_from_config_file()

    print("\n" + "═" * 70)
    print("RESULTADO FINAL")
    print("═" * 70)
    for name, passed in results.items():
        status = "✓ PASADO" if passed else "✗ FALLIDO"
        print(f"  {status} - {name}")

    if all(results.values()):
        print("\n🎉 Todos los tests MCP pasaron!")
    else:
        print("\n⚠️  Algunos tests fallaron.")


if __name__ == "__main__":
    asyncio.run(main())
