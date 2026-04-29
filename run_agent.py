"""Corre o agente real (OpenAI Agents SDK) - um ciclo completo.
O agente decide sozinho o que recolher, processar e resumir.
Corre com: python run_agent.py
"""
import asyncio

from src.db import init_db
from src.agent.hermes_agent import run_hermes_once


if __name__ == "__main__":
    print("A iniciar Hermes Energy Agent...")
    init_db()
    output = asyncio.run(run_hermes_once())
    print("\n" + "=" * 60)
    print("RESULTADO DO AGENTE:")
    print("=" * 60)
    print(output)
