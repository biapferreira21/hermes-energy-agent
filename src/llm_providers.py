import requests
from openai import OpenAI

from src.settings import settings


class LLMClient:
    """Camada unica para trocar de LLM sem mudar o resto do codigo.
    Define LLM_PROVIDER=openai | openrouter | ollama no ficheiro .env
    """

    def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        provider = settings.llm_provider.lower()
        if provider == "openai":
            return self._openai(system, user, json_mode)
        if provider == "openrouter":
            return self._openrouter(system, user, json_mode)
        if provider == "ollama":
            return self._ollama(system, user, json_mode)
        raise ValueError(f"LLM_PROVIDER desconhecido: '{provider}'. Usa openai, openrouter ou ollama.")

    # ------------------------------------------------------------------
    # OpenAI (Chat Completions API - mais estavel e documentada)
    # ------------------------------------------------------------------
    def _openai(self, system: str, user: str, json_mode: bool) -> str:
        client = OpenAI(api_key=settings.openai_api_key)
        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **kwargs,
        )
        return response.choices[0].message.content or ""

    # ------------------------------------------------------------------
    # OpenRouter (roteador de modelos baratos/alternativos)
    # ------------------------------------------------------------------
    def _openrouter(self, system: str, user: str, json_mode: bool) -> str:
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Hermes Energy Agent",
        }
        payload: dict = {
            "model": settings.openrouter_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    # ------------------------------------------------------------------
    # Ollama (modelos locais, gratuito, sem internet)
    # ------------------------------------------------------------------
    def _ollama(self, system: str, user: str, json_mode: bool) -> str:
        prompt = f"SYSTEM:\n{system}\n\nUSER:\n{user}"
        if json_mode:
            prompt += "\n\nResponde APENAS com JSON valido. Nao adicionar texto antes ou depois do JSON."
        payload = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
        }
        r = requests.post(
            f"{settings.ollama_base_url}/api/generate",
            json=payload,
            timeout=120,
        )
        r.raise_for_status()
        return r.json().get("response", "")


# Instancia global - usa-se como: from src.llm_providers import llm
llm = LLMClient()
