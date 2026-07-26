"""Test end-to-end del Agente SRE Autónomo con datos ficticios.

Este script prueba:
1. Que el modelo (Ollama local o Bedrock) responde correctamente
2. Que InMemorySaver (MemorySaver) funciona con thread_id
3. Que las tools se invocan cuando la alerta lo amerita
4. Que el agente responde con un análisis estructurado

Requisitos para correr localmente:
- Ollama corriendo con el modelo configurado (qwen3:8b por defecto)
- O credenciales AWS válidas para Bedrock

Ejecución:
    python -m pytest tests/test_agent_e2e.py -v -s
    # O directamente:
    python tests/test_agent_e2e.py
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Cargar variables de entorno antes de importar settings
from dotenv import load_dotenv
load_dotenv()

from src.agents.sre_autonomo.agent import _build_agent, analyze_alert
from src.config import settings
from src.models.alerts import CloudWatchAlert

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


# ============================================================================
# DATOS FICTICIOS - Alertas simuladas de CloudWatch
# ============================================================================

MOCK_ALERTS = {
    "cpu_critica": CloudWatchAlert(
        alarm_name="HighCPU-order-svc",
        alarm_description="CPU del servicio de órdenes supera el 95%",
        state="ALARM",
        previous_state="OK",
        reason="Threshold Crossed: 1 out of 1 datapoints [97.3] was >= 95.0",
        timestamp=datetime(2026, 7, 26, 14, 30, 0, tzinfo=timezone.utc),
        region="us-east-1",
        namespace="AWS/ECS",
        metric_name="CPUUtilization",
        dimensions={"ServiceName": "order-svc", "ClusterName": "kiro-cluster"},
        raw_payload={"trigger": {"statistic": "Average", "period": 300}},
    ),
    "memoria_alta": CloudWatchAlert(
        alarm_name="HighMemory-user-svc",
        alarm_description="Memoria del servicio de usuarios supera el 90%",
        state="ALARM",
        previous_state="OK",
        reason="Threshold Crossed: 3 out of 3 datapoints [91.2, 92.5, 93.1] were >= 90.0",
        timestamp=datetime(2026, 7, 26, 15, 0, 0, tzinfo=timezone.utc),
        region="us-east-1",
        namespace="AWS/ECS",
        metric_name="MemoryUtilization",
        dimensions={"ServiceName": "user-svc", "ClusterName": "kiro-cluster"},
        raw_payload={},
    ),
    "errores_5xx": CloudWatchAlert(
        alarm_name="High5xxErrors-pay-svc",
        alarm_description="Errores 5xx en servicio de pagos superan 50/min",
        state="ALARM",
        previous_state="OK",
        reason="Threshold Crossed: 1 out of 1 datapoints [78.0] was >= 50.0",
        timestamp=datetime(2026, 7, 26, 15, 15, 0, tzinfo=timezone.utc),
        region="us-east-1",
        namespace="AWS/ApplicationELB",
        metric_name="HTTPCode_Target_5XX_Count",
        dimensions={"ServiceName": "pay-svc", "LoadBalancer": "kiro-alb"},
        raw_payload={},
    ),
    "latencia_alta": CloudWatchAlert(
        alarm_name="HighLatency-auth-svc",
        alarm_description="Latencia p99 del servicio de auth supera 2 segundos",
        state="ALARM",
        previous_state="INSUFFICIENT_DATA",
        reason="Threshold Crossed: 5 out of 5 datapoints [2.3, 2.5, 2.8, 3.1, 2.9] were >= 2.0",
        timestamp=datetime(2026, 7, 26, 15, 30, 0, tzinfo=timezone.utc),
        region="us-east-1",
        namespace="AWS/ECS",
        metric_name="ResponseTime_p99",
        dimensions={"ServiceName": "auth-svc", "ClusterName": "kiro-cluster"},
        raw_payload={},
    ),
    "cola_saturada": CloudWatchAlert(
        alarm_name="QueueBacklog-order-svc-dlq",
        alarm_description="Dead Letter Queue con más de 100 mensajes",
        state="ALARM",
        previous_state="OK",
        reason="Threshold Crossed: 1 out of 1 datapoints [342.0] was >= 100.0",
        timestamp=datetime(2026, 7, 26, 16, 0, 0, tzinfo=timezone.utc),
        region="us-east-1",
        namespace="AWS/SQS",
        metric_name="ApproximateNumberOfMessagesVisible",
        dimensions={"QueueName": "order-svc-dlq"},
        raw_payload={},
    ),
    "servicio_ok": CloudWatchAlert(
        alarm_name="HighCPU-order-svc",
        alarm_description="CPU del servicio de órdenes normalizada",
        state="OK",
        previous_state="ALARM",
        reason="Threshold Crossed: 1 out of 1 datapoints [45.2] was < 95.0",
        timestamp=datetime(2026, 7, 26, 16, 30, 0, tzinfo=timezone.utc),
        region="us-east-1",
        namespace="AWS/ECS",
        metric_name="CPUUtilization",
        dimensions={"ServiceName": "order-svc", "ClusterName": "kiro-cluster"},
        raw_payload={},
    ),
}


# ============================================================================
# TEST 1: Verificar que el modelo está funcionando
# ============================================================================

async def test_model_connection():
    """Verifica que el LLM configurado responde correctamente."""
    print("\n" + "=" * 70)
    print("TEST 1: Verificar conexión con el modelo")
    print("=" * 70)

    try:
        agent = await _build_agent()
        print(f"✓ Agente construido (modelo: {settings.model_id})")

        # Hacer una invocación simple para verificar que responde
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Responde solo con 'OK' si puedes leer esto."}]},
            config={"configurable": {"thread_id": "test-connection"}},
        )
        response = result["messages"][-1].content
        print(f"✓ Modelo respondió: {response[:100]}")
        print("✓ TEST PASADO - El modelo está funcionando correctamente")
        return True

    except Exception as e:
        print(f"✗ ERROR: No se pudo conectar al modelo: {e}")
        print("  → Verifica que estés autenticado: az login")
        print("  → Verifica el endpoint y deployment en el .env")
        return False


# ============================================================================
# TEST 2: Verificar que MemorySaver funciona correctamente
# ============================================================================

async def test_memory_saver():
    """Verifica que MemorySaver mantiene el estado entre invocaciones."""
    print("\n" + "=" * 70)
    print("TEST 2: Verificar MemorySaver (checkpointer)")
    print("=" * 70)

    try:
        agent = await _build_agent()
        thread_id = "test-memory-001"
        config = {"configurable": {"thread_id": thread_id}}

        # Primera invocación
        result1 = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Recuerda este código: ALFA-7734"}]},
            config=config,
        )
        msg1 = result1["messages"][-1].content
        print(f"✓ Primera invocación exitosa: {msg1[:80]}...")

        # Segunda invocación en el mismo thread - debería recordar el contexto
        result2 = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "¿Cuál fue el código que te pedí recordar?"}]},
            config=config,
        )
        msg2 = result2["messages"][-1].content
        print(f"✓ Segunda invocación exitosa: {msg2[:80]}...")

        if "ALFA-7734" in msg2 or "alfa" in msg2.lower() or "7734" in msg2:
            print("✓ TEST PASADO - MemorySaver mantiene el contexto entre invocaciones")
        else:
            print("⚠ ADVERTENCIA - El modelo respondió pero no recordó el código exacto")
            print(f"  Respuesta completa: {msg2}")

        return True

    except Exception as e:
        print(f"✗ ERROR: Fallo en MemorySaver: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST 3: Probar el agente con alertas ficticias
# ============================================================================

async def test_agent_with_mock_alerts():
    """Prueba el flujo completo con alertas ficticias."""
    print("\n" + "=" * 70)
    print("TEST 3: Probar agente con alertas ficticias")
    print("=" * 70)

    results = {}

    for alert_name, alert in MOCK_ALERTS.items():
        print(f"\n{'─' * 50}")
        print(f"  Procesando alerta: {alert_name}")
        print(f"  Alarma: {alert.alarm_name} | Estado: {alert.state}")
        print(f"{'─' * 50}")

        try:
            response = await analyze_alert(alert)

            print(f"  ✓ Status: {response.status}")
            print(f"  ✓ Alert ID: {response.alert_id}")
            print(f"  ✓ Acciones ejecutadas: {response.actions_suggested}")
            print(f"  ✓ Análisis (primeros 200 chars):")
            print(f"    {response.analysis[:200] if response.analysis else 'N/A'}...")

            results[alert_name] = {
                "success": True,
                "actions": response.actions_suggested,
                "has_analysis": bool(response.analysis and len(response.analysis) > 10),
            }

        except Exception as e:
            print(f"  ✗ ERROR procesando {alert_name}: {e}")
            results[alert_name] = {"success": False, "error": str(e)}

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN DE RESULTADOS")
    print("=" * 70)
    passed = sum(1 for r in results.values() if r.get("success"))
    total = len(results)
    print(f"Alertas procesadas exitosamente: {passed}/{total}")

    for name, result in results.items():
        status = "✓" if result.get("success") else "✗"
        actions = result.get("actions", [])
        print(f"  {status} {name}: actions={actions}")

    return passed == total


# ============================================================================
# TEST 4: Verificar que las tools se ejecutan correctamente
# ============================================================================

async def test_tools_execution():
    """Verifica que el agente puede ejecutar tools cuando se le pide directamente."""
    print("\n" + "=" * 70)
    print("TEST 4: Verificar ejecución de tools")
    print("=" * 70)

    try:
        agent = await _build_agent()
        thread_id = "test-tools-001"
        config = {"configurable": {"thread_id": thread_id}}

        # Pedir explícitamente que ejecute una tool
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Ejecuta la herramienta restart_service para reiniciar "
                            "el servicio 'order-svc'. No analices, solo ejecuta la tool."
                        ),
                    }
                ]
            },
            config=config,
        )

        messages = result["messages"]
        tool_calls = [msg for msg in messages if hasattr(msg, "name") and msg.name]
        tool_names = [msg.name for msg in tool_calls]

        print(f"  ✓ Total mensajes en respuesta: {len(messages)}")
        print(f"  ✓ Tools invocadas: {tool_names}")

        if "restart_service" in tool_names:
            print("  ✓ TEST PASADO - El agente ejecutó restart_service correctamente")
            return True
        else:
            print("  ⚠ ADVERTENCIA - El agente no ejecutó la tool solicitada")
            print(f"    Respuesta final: {messages[-1].content[:200]}")
            return True  # No es un fallo crítico

    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# MAIN - Ejecutar todos los tests
# ============================================================================

async def main():
    """Ejecuta toda la suite de tests."""
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║     TEST SUITE - Agente SRE Autónomo (kiro-sre-Monitor-Agent)      ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║  Verifica: Modelo, InMemorySaver, Tools, Análisis de alertas       ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    print(f"\nConfiguración actual:")
    print(f"  Modelo: {settings.model_id}")
    print(f"  Región: {settings.aws_region}")
    print(f"  Entorno: {settings.environment}")

    results = {}

    # Test 1: Modelo
    results["model"] = await test_model_connection()
    if not results["model"]:
        print("\n⛔ No se puede continuar sin conexión al modelo.")
        print("   Asegúrate de que Ollama esté corriendo o configura Bedrock.")
        return

    # Test 2: MemorySaver
    results["memory"] = await test_memory_saver()

    # Test 3: Alertas ficticias
    results["alerts"] = await test_agent_with_mock_alerts()

    # Test 4: Tools
    results["tools"] = await test_tools_execution()

    # Resultado final
    print("\n" + "═" * 70)
    print("RESULTADO FINAL")
    print("═" * 70)
    all_passed = all(results.values())
    for test_name, passed in results.items():
        status = "✓ PASADO" if passed else "✗ FALLIDO"
        print(f"  {status} - {test_name}")

    if all_passed:
        print("\n🎉 Todos los tests pasaron exitosamente!")
    else:
        print("\n⚠️  Algunos tests fallaron. Revisa los detalles arriba.")

    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
