"""Scoring de relevancia para investimento — 0 a 100.

Hierarquia de valor:
  Tier 1 — Instrumentos financeiros de energia + grandes players + blockchain/energia
  Tier 2 — Noticias com impacto financeiro medio
  Tier 3 — Ruido / noticias sem impacto financeiro directo
"""
import yaml
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _load_major_players() -> frozenset[str]:
    """Carrega a lista de grandes players de entities.yaml para comparacao rapida."""
    try:
        cfg = yaml.safe_load(Path("config/entities.yaml").read_text(encoding="utf-8"))
        players: set[str] = set()
        # Grupos de alta relevancia: majors, traders, bancos
        for group in ("energy_majors", "commodity_traders", "banks_financial_institutions",
                      "exchanges_markets", "blockchain_tokenization"):
            for name in cfg.get(group, []):
                players.add(name.lower())
        return frozenset(players)
    except Exception:
        return frozenset()


@lru_cache(maxsize=1)
def _load_high_value_instruments() -> frozenset[str]:
    """Carrega instrumentos de alto valor financeiro da taxonomy."""
    try:
        cfg = yaml.safe_load(Path("config/taxonomy.yaml").read_text(encoding="utf-8"))
        instruments: set[str] = set()
        asset_classes = cfg.get("asset_classes", {})
        for ac_data in asset_classes.values():
            for instr in ac_data.get("instruments", []):
                instruments.add(instr.lower())
        return frozenset(instruments)
    except Exception:
        return frozenset()


_SOURCE_BONUS = {"high": 8, "medium": 4, "low": 1}

_HIGH_MARKET_LAYERS = {
    "front_office_trading", "exchange_execution", "otc_execution",
    "clearing", "settlement", "trade_finance",
}
_MED_MARKET_LAYERS = {"post_trade", "custody", "risk_management"}

_HIGH_BLOCKCHAIN = {
    "tokenization", "stablecoin_settlement", "tokenized_deposits",
    "carbon_credit_tokenization", "rwa_infrastructure",
}
_MED_BLOCKCHAIN = {"smart_contracts", "post_trade_reconciliation"}

_PRICE_DRIVERS = {"supply", "demand", "geopolitical", "regulatory", "financial", "corporate"}
_DIRECTIONAL_SENTIMENT = {"bullish", "bearish", "mixed"}


def score_item(classification: dict, source_priority: str = "medium") -> int:
    """Calcula score de investimento 0-100.

    classification : dicionario devolvido pelo classify()
    source_priority: 'high' | 'medium' | 'low' (de sources.yaml)
    """
    score = 0
    major_players = _load_major_players()
    high_value_instruments = _load_high_value_instruments()

    # ----------------------------------------------------------------
    # 1. RELEVANCIA FINANCEIRA DIRECTA (0-30 pts)
    # ----------------------------------------------------------------
    fin = classification.get("financial_relevance", "low")
    score += {"high": 30, "medium": 16, "low": 4}.get(fin, 4)

    # ----------------------------------------------------------------
    # 2. GRANDES PLAYERS ENVOLVIDOS (0-20 pts)
    # Bonus extra se sao as empresas/instituicoes de topo
    # ----------------------------------------------------------------
    companies = classification.get("companies", []) or []
    institutions = classification.get("institutions", []) or []
    all_actors = [str(a).lower() for a in (companies + institutions) if a]

    major_hit = sum(1 for a in all_actors if a in major_players)
    minor_hit = len(all_actors) - major_hit

    score += min(major_hit * 8, 16)   # ate 16 pts por majors
    score += min(minor_hit * 2, 4)    # ate 4 pts por outros

    # ----------------------------------------------------------------
    # 3. INSTRUMENTOS FINANCEIROS ESPECIFICOS (0-18 pts)
    # Maior bonus se sao instrumentos de alto valor da taxonomy
    # ----------------------------------------------------------------
    instruments = classification.get("instruments", []) or []
    instr_lower = [str(i).lower() for i in instruments if i]

    hv_match = sum(1 for i in instr_lower if i in high_value_instruments)
    other_instr = len(instr_lower) - hv_match

    score += min(hv_match * 7, 14)    # ate 14 pts por instrumentos da taxonomy
    score += min(other_instr * 2, 4)  # ate 4 pts por outros instrumentos

    # ----------------------------------------------------------------
    # 4. DRIVER DE PRECO IDENTIFICADO (0-12 pts)
    # Noticias com driver claro sao mais accionaveis
    # ----------------------------------------------------------------
    driver = classification.get("price_driver", "none")
    if driver in _PRICE_DRIVERS:
        score += 12
    else:
        score += 2

    # ----------------------------------------------------------------
    # 5. SENTIMENTO DE MERCADO DIRECCIONAL (0-8 pts)
    # ----------------------------------------------------------------
    sentiment = classification.get("market_sentiment", "unclear")
    if sentiment in _DIRECTIONAL_SENTIMENT:
        score += 8
    elif sentiment == "neutral":
        score += 3

    # ----------------------------------------------------------------
    # 6. CAMADA DE MERCADO AFECTADA (0-7 pts)
    # ----------------------------------------------------------------
    layer = classification.get("market_layer", "")
    if layer in _HIGH_MARKET_LAYERS:
        score += 7
    elif layer in _MED_MARKET_LAYERS:
        score += 4
    else:
        score += 1

    # ----------------------------------------------------------------
    # 7. QUALIDADE DA FONTE (0-8 pts)
    # ----------------------------------------------------------------
    score += _SOURCE_BONUS.get(source_priority, 4)

    # ----------------------------------------------------------------
    # 8. BLOCKCHAIN/TOKENIZACAO em contexto de energia (0-5 pts)
    # Factor menor — so relevante se combinado com energia/commodities
    # ----------------------------------------------------------------
    br = classification.get("blockchain_relation", "none")
    asset_classes = classification.get("asset_classes", []) or []
    has_energy = any(ac in {"oil", "gas_lng", "power", "renewables", "carbon"}
                     for ac in asset_classes)

    if br in _HIGH_BLOCKCHAIN and has_energy:
        score += 5
    elif br in _MED_BLOCKCHAIN and has_energy:
        score += 3
    elif br in _HIGH_BLOCKCHAIN:
        score += 2  # blockchain sem energia = valor limitado

    # ----------------------------------------------------------------
    # Ajuste pela confianca do classificador (minimo 40%)
    # ----------------------------------------------------------------
    confidence = float(classification.get("confidence_score", 0.5) or 0.5)
    score = int(score * max(0.4, min(confidence, 1.0)))

    return min(score, 100)
