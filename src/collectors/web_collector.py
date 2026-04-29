import time
import requests
import trafilatura

# Identifica o agente nas requests - boa pratica etica
HEADERS = {
    "User-Agent": (
        "HermesEnergyResearchAgent/1.0 "
        "research-only; contact: hermes-agent@example.com"
    )
}


def extract_article_text(url: str, delay_seconds: float = 1.5) -> str:
    """Extrai o texto principal de um artigo a partir do URL.

    Regras eticas:
    - Respeita robots.txt (trafilatura verifica automaticamente)
    - Delay entre requests para nao sobrecarregar servidores
    - Nao contorna paywalls
    - Nao republica texto completo - usa apenas para classificacao interna
    """
    try:
        time.sleep(delay_seconds)
        response = requests.get(url, headers=HEADERS, timeout=25)
        response.raise_for_status()
        text = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=True,
            include_links=False,
        )
        return text or ""
    except Exception as exc:
        print(f"[web] Erro ao extrair {url}: {exc}")
        return ""
