"""
CloudWatch MCP Server — Kiro SRE Agent
=======================================
Servidor MCP (Model Context Protocol) que expone herramientas de CloudWatch
para que el Kiro IDE y el agente Carmen puedan consultar logs en tiempo real.

Protocolo: JSON-RPC 2.0 via stdin/stdout (estándar MCP).

Herramientas expuestas:
  get_recent_errors    → Últimos errores del log group del Backend
  get_service_health   → Estado de salud de un microservicio
  get_incident_summary → Resumen de incidentes de la sesión actual

Para activarlo desde Kiro IDE: configurado en .kiro/settings/mcp.json
Para ejecutarlo manualmente:   python src/mcp/cloudwatch_mcp_server.py
"""

import json
import os
import sys
import time
import boto3
from typing import Any


AWS_REGION = os.getenv("KIRO_AWS_REGION", "us-east-1")
LOG_GROUP = os.getenv("KIRO_LOG_GROUP_NAME", "/kiro/microservices/backend")
AWS_KEY = os.getenv("KIRO_AWS_ACCESS_KEY_ID", "")
AWS_SECRET = os.getenv("KIRO_AWS_SECRET_ACCESS_KEY", "")


def _cw_client():
    kw: dict[str, Any] = {"region_name": AWS_REGION}
    if AWS_KEY:
        kw["aws_access_key_id"] = AWS_KEY
    if AWS_SECRET:
        kw["aws_secret_access_key"] = AWS_SECRET
    return boto3.client("logs", **kw)


# ── Herramientas ────────────────────────────────────────────────────────────

def get_recent_errors(limit: int = 20, minutes: int = 60) -> dict:
    """Obtiene los últimos N errores del log group del Backend desde CloudWatch."""
    try:
        client = _cw_client()
        now_ms = int(time.time() * 1000)
        start_ms = now_ms - minutes * 60 * 1000

        resp = client.filter_log_events(
            logGroupName=LOG_GROUP,
            filterPattern='{ $.level = "ERROR" }',
            startTime=start_ms,
            endTime=now_ms,
            limit=min(limit, 100),
        )

        errors = []
        for ev in resp.get("events", []):
            try:
                data = json.loads(ev["message"])
                errors.append({
                    "timestamp": data.get("timestamp"),
                    "service": data.get("service"),
                    "error_type": data.get("error_type"),
                    "status_code": data.get("status_code"),
                    "message": data.get("message"),
                    "trace_id": data.get("trace_id"),
                    "duration_ms": data.get("duration_ms"),
                })
            except (json.JSONDecodeError, KeyError):
                pass

        return {"total": len(errors), "errors": errors, "log_group": LOG_GROUP}
    except Exception as exc:
        return {"error": str(exc), "errors": [], "note": "Verify AWS credentials in .env"}


def get_service_health(service_name: str, minutes: int = 15) -> dict:
    """Calcula error rate y latencia promedio de un servicio en los últimos N minutos."""
    try:
        client = _cw_client()
        now_ms = int(time.time() * 1000)
        start_ms = now_ms - minutes * 60 * 1000

        resp = client.filter_log_events(
            logGroupName=LOG_GROUP,
            filterPattern=f'{{ $.service = "{service_name}" }}',
            startTime=start_ms,
            endTime=now_ms,
            limit=200,
        )

        total = errors = 0
        durations: list[float] = []

        for ev in resp.get("events", []):
            try:
                data = json.loads(ev["message"])
                total += 1
                if data.get("level") == "ERROR":
                    errors += 1
                dur = data.get("duration_ms")
                if dur is not None:
                    durations.append(float(dur))
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

        error_rate = round(errors / total * 100, 2) if total else 0
        avg_lat = round(sum(durations) / len(durations), 2) if durations else 0

        if error_rate > 20 or avg_lat > 3000:
            status = "critical"
        elif error_rate > 5 or avg_lat > 800:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "service": service_name,
            "status": status,
            "total_requests": total,
            "error_count": errors,
            "error_rate_pct": error_rate,
            "avg_latency_ms": avg_lat,
            "window_minutes": minutes,
        }
    except Exception as exc:
        return {"error": str(exc), "service": service_name, "status": "unknown"}


def get_incident_summary() -> dict:
    """Devuelve el resumen de incidentes analizados en la sesión actual del agente."""
    try:
        # Importa desde el orquestador en memoria (si el servidor MCP corre en el mismo proceso)
        from src.agents.orchestrator import get_incident_summary as _summary
        return _summary()
    except ImportError:
        return {"note": "Run as standalone MCP server — incident data not available"}


# ── Protocolo MCP JSON-RPC 2.0 ──────────────────────────────────────────────

TOOLS: dict[str, dict] = {
    "get_recent_errors": {
        "description": "Obtiene los últimos errores (level=ERROR) del Backend desde CloudWatch Logs",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20, "description": "Máximo de errores a retornar"},
                "minutes": {"type": "integer", "default": 60, "description": "Ventana temporal en minutos"},
            },
        },
        "fn": get_recent_errors,
    },
    "get_service_health": {
        "description": "Estado de salud de un microservicio: error rate, latencia y status (healthy/degraded/critical)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Nombre del servicio (ej: sales-service)"},
                "minutes": {"type": "integer", "default": 15, "description": "Ventana temporal en minutos"},
            },
            "required": ["service_name"],
        },
        "fn": get_service_health,
    },
    "get_incident_summary": {
        "description": "Resumen de incidentes analizados por el agente en la sesión actual",
        "inputSchema": {"type": "object", "properties": {}},
        "fn": lambda: get_incident_summary(),
    },
}


def _send(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _handle(req: dict) -> None:
    method = req.get("method", "")
    req_id = req.get("id")

    if method == "initialize":
        _send({
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "kiro-cloudwatch-mcp", "version": "1.0.0"},
            },
        })
    elif method == "tools/list":
        _send({
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "tools": [
                    {"name": n, "description": m["description"], "inputSchema": m["inputSchema"]}
                    for n, m in TOOLS.items()
                ]
            },
        })
    elif method == "tools/call":
        params = req.get("params", {})
        name = params.get("name", "")
        args = params.get("arguments", {})
        if name not in TOOLS:
            _send({"jsonrpc": "2.0", "id": req_id,
                   "error": {"code": -32601, "message": f"Tool '{name}' not found"}})
            return
        try:
            result = TOOLS[name]["fn"](**args)
            _send({"jsonrpc": "2.0", "id": req_id,
                   "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}})
        except Exception as exc:
            _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(exc)}})
    elif method == "notifications/initialized":
        pass
    elif req_id is not None:
        _send({"jsonrpc": "2.0", "id": req_id,
               "error": {"code": -32601, "message": f"Method '{method}' not found"}})


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if line:
            try:
                _handle(json.loads(line))
            except json.JSONDecodeError:
                pass


if __name__ == "__main__":
    main()
