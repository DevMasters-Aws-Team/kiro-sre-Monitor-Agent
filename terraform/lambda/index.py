"""Lambda Handler - Entry point para AWS Lambda."""

import json
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def lambda_handler(event, context):
    """Handler principal de Lambda para el agente Kiro."""
    print(f"Evento recibido: {json.dumps(event)}")

    try:
        # Importar después de agregar al path
        from src.agents.event_handler import event_handler

        # Procesar evento de forma asíncrona
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(event_handler.handle_event(event))
        loop.close()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Evento procesado exitosamente",
                "result": result,
                "knowledge_table": os.getenv("KNOWLEDGE_TABLE"),
                "tickets_table": os.getenv("TICKETS_TABLE"),
                "incidents_table": os.getenv("INCIDENTS_TABLE"),
            }),
        }

    except Exception as e:
        print(f"Error procesando evento: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Error procesando evento",
                "error": str(e),
            }),
        }
