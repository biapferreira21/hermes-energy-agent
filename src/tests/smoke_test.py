"""Teste rapido para verificar que o LLM responde correctamente.
Corre com: python -m src.tests.smoke_test
"""
from src.llm_providers import llm
from src.settings import settings


def run_smoke_test() -> None:
    print(f"Provider: {settings.llm_provider}")
    print(f"Modelo: {settings.openai_model if settings.llm_provider == 'openai' else settings.ollama_model}")
    print("A testar ligacao ao LLM...")

    system = "You are a helpful assistant. Answer concisely."
    user = "Say exactly: 'Hermes Energy Agent is ready.' and nothing else."

    response = llm.complete(system, user)
    print(f"Resposta: {response}")
    print("OK - LLM responde correctamente!")


if __name__ == "__main__":
    run_smoke_test()
