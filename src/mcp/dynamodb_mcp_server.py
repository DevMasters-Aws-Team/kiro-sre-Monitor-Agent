"""
DynamoDB MCP Server — Kiro SRE Agent
=====================================
Expone la Knowledge Base de errores conocidos via protocolo MCP.
Permite al Kiro IDE consultar soluciones almacenadas en DynamoDB.

Herramientas:
  query_knowledge_base  → Busca solución para un tipo de error
  list_known_errors     → Lista todos los errores en la KB
"""

import json
import os
import sys
import boto3
from typing import Any


AWS_REGION = os.getenv("KIRO_AWS_REGION", "us-east-1")
KNOWLEDGE_TABLE = os.getenv("KIRO_KNOWLEDGE_TABLE", "kiro-dev-KnowledgeTable")
AWS_KEY = os.getenv("KIRO_AWS_ACCESS_KEY_ID", "")
AWS_SECRET = os.getenv("KIRO_AWS_SECRET_ACCESS_KEY", "")


def _dynamo_resource():
    kw: dict[str, Any] = {"region_name": AWS_REGION}
    if AWS_KEY:
        kw["aws_access_key_id"] = AWS_KEY
    if AWS_SECRET:
        kw["aws_secret_access_key"] = AWS_SECRET
    return boto3.resource("dynamodb", **kw)


def query_knowledge_base(error_type: str, service: str = "") -> dict:
    """Busca una solución conocida en DynamoDB KnowledgeTable."""
    try:
        table = _dynamo_resource().Table(KNOWLEDGE_TABLE)
        if service:
            resp = table.get_item(Key={"errorType": error_type, "service": service})
            item = resp.get("Item")
            if item:
                return {"found": True, "error_type": error_type, "service": service,
                        "solution": item.get("solution", {}),
                        "confidence": float(item.get("confidence", 0.8)),
                        "occurrences": int(item.get("occurrences", 1))}
        # Fallback: buscar cualquier servicio
        resp = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("errorType").eq(error_type),
            Limit=3,
        )
        items = resp.get("Items", [])
        if items:
            best = max(items, key=lambda x: float(x.get("confidence", 0)))
            return {"found": True, "error_type": error_type, "service": best.get("service"),
                    "solution": best.get("solution", {}),
                    "confidence": float(best.get("confidence", 0.8))}
        return {"found": False, "error_type": error_type,
                "message": "No solution found in knowledge base"}
    except Exception as exc:
        return {"error": str(exc), "found": False}


def list_known_errors(limit: int = 20) -> dict:
    """Lista los errores conocidos en la Knowledge Base."""
    try:
        table = _dynamo_resource().Table(KNOWLEDGE_TABLE)
        resp = table.scan(Limit=limit)
        items = resp.get("Items", [])
        return {
            "total": len(items),
            "known_errors": [
                {"error_type": i.get("errorType"), "service": i.get("service"),
                 "confidence": float(i.get("confidence", 0)),
                 "occurrences": int(i.get("occurrences", 0))}
                for i in items
            ],
        }
    except Exception as exc:
        return {"error": str(exc), "known_errors": []}


TOOLS: dict[str, dict] = {
    "query_knowledge_base": {
        "description": "Busca solución conocida en DynamoDB KnowledgeTable para un tipo de error específico",
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_type": {"type": "string", "description": "Tipo de error (ej: DatabaseTimeoutError)"},
                "service": {"type": "string", "default": "", "description": "Servicio afectado (opcional)"},
            },
            "required": ["error_type"],
        },
        "fn": query_knowledge_base,
    },
    "list_known_errors": {
        "description": "Lista todos los errores conocidos y sus soluciones almacenadas en la Knowledge Base",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20, "description": "Máximo de registros"}
            },
        },
        "fn": list_known_errors,
    },
}


def _send(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _handle(req: dict) -> None:
    method = req.get("method", "")
    req_id = req.get("id")
    if method == "initialize":
        _send({"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "kiro-dynamodb-mcp", "version": "1.0.0"},
        }})
    elif method == "tools/list":
        _send({"jsonrpc": "2.0", "id": req_id, "result": {
            "tools": [{"name": n, "description": m["description"], "inputSchema": m["inputSchema"]}
                      for n, m in TOOLS.items()]
        }})
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
