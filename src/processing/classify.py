import json

from src.llm_providers import llm
from src.settings import settings

SYSTEM_PROMPT = """\
You are Hermes Energy & Investment Classifier.

Your job is to identify the INVESTMENT SIGNAL VALUE of an article for a professional
who trades and invests in energy commodities, energy equities, and related financial instruments.

== WHAT MAKES financial_relevance = "high" ==
An article has HIGH financial relevance if it directly affects prices, positions, or capital flows in:

OIL & GAS INSTRUMENTS:
- Crude oil (Brent, WTI, Dubai): production cuts/hikes, inventory data, refinery outages, cargo diversions
- Natural gas & LNG: TTF, Henry Hub, JKM price moves, supply disruptions, new long-term contracts
- Oil & gas equities, bonds, ETFs: major company results, M&A, capex changes, credit events
- Futures, options, swaps on any of the above

POWER & RENEWABLES INSTRUMENTS:
- Power prices (day-ahead, intraday, futures), spark spreads, capacity auctions
- PPAs, green bonds, renewable project finance at scale (>$100M)
- Battery storage, hydrogen: only if a major financial transaction or infrastructure decision

CARBON & CLIMATE INSTRUMENTS:
- EU ETS (EUA), UK ETS, California/RGGI allowances: price moves, policy changes, supply/demand
- Voluntary carbon credits: large trades, registry decisions, ICVCM/VCMI standards changes

FINANCIAL & MACRO EVENTS:
- Central bank decisions, inflation, USD moves that directly affect energy commodity prices
- Major financial institution (JPMorgan, Goldman, Citi, HSBC, Macquarie, etc.) entering/exiting energy
- Sovereign wealth funds, PE, infrastructure funds making large energy investments

BLOCKCHAIN & TOKENIZATION (energy-specific only):
- Tokenization of oil cargo, LNG contracts, carbon credits, PPAs, trade documents
- Stablecoin/CBDC settlement of commodity trades
- Post-trade infrastructure for energy markets (VAKT, Komgo, Fnality)

== WHAT MAKES financial_relevance = "medium" ==
- Energy policy/regulation that will affect markets in 6-24 months
- New energy projects (if large-scale with named investors/developers)
- Company strategy announcements without immediate financial impact
- Blockchain/DLT projects in early stages

== WHAT MAKES financial_relevance = "low" ==
- Pure technology news (solar efficiency records, new battery chemistry) WITHOUT financial transactions
- General climate/ESG commentary without specific instruments or transactions
- Crypto/blockchain news with NO energy or commodity connection
- Operational/safety news without market impact

== KEY RULES ==
1. financial_relevance = "high" requires: a SPECIFIC financial instrument OR a MAJOR player making a market-moving decision
2. instruments list = ONLY tradeable instruments mentioned (futures contracts, ETFs, physical cargo, allowances, bonds). NOT company names.
3. companies list = ONLY company names (Shell, BP, Vitol, JPMorgan, etc.)
4. market_sentiment must reflect price direction for the PRIMARY instrument affected
5. price_driver = dominant force causing the market move
6. Blockchain does NOT automatically mean tokenization or high relevance

CRITICAL - blockchain_relation MUST be exactly one of:
none | blockchain_data_layer | digital_documents | smart_contracts |
post_trade_reconciliation | tokenization | stablecoin_settlement |
tokenized_deposits | carbon_credit_tokenization | rwa_infrastructure | unclear

CRITICAL - price_driver MUST be exactly one of:
supply | demand | geopolitical | regulatory | financial | corporate | none

CRITICAL - market_sentiment MUST be exactly one of:
bullish | bearish | neutral | mixed | unclear

CRITICAL - time_horizon MUST be exactly one of:
immediate | short_term | medium_term | long_term | unclear

Return ONLY valid JSON. No text before or after.
"""

_VALID_BLOCKCHAIN = {
    "none", "blockchain_data_layer", "digital_documents", "smart_contracts",
    "post_trade_reconciliation", "tokenization", "stablecoin_settlement",
    "tokenized_deposits", "carbon_credit_tokenization", "rwa_infrastructure", "unclear",
}
_VALID_PRICE_DRIVER = {
    "supply", "demand", "geopolitical", "regulatory", "financial", "corporate", "none",
}
_VALID_SENTIMENT = {"bullish", "bearish", "neutral", "mixed", "unclear"}
_VALID_HORIZON = {"immediate", "short_term", "medium_term", "long_term", "unclear"}

_BLOCKCHAIN_MAP = {
    "tokeniz": "tokenization",
    "stablecoin": "stablecoin_settlement",
    "cbdc": "stablecoin_settlement",
    "digital money": "stablecoin_settlement",
    "smart contract": "smart_contracts",
    "rwa": "rwa_infrastructure",
    "real world asset": "rwa_infrastructure",
    "carbon credit": "carbon_credit_tokenization",
    "carbon token": "carbon_credit_tokenization",
    "reconcili": "post_trade_reconciliation",
    "document": "digital_documents",
    "data layer": "blockchain_data_layer",
    "oracle": "blockchain_data_layer",
}


def _normalise(value: str, valid_set: set, keyword_map: dict | None = None) -> str:
    if not value:
        return "unclear" if "unclear" in valid_set else list(valid_set)[0]
    v = value.strip().lower()
    if v in valid_set:
        return v
    if keyword_map:
        for kw, mapped in keyword_map.items():
            if kw in v:
                return mapped
    return "unclear" if "unclear" in valid_set else "none"


_FALLBACK: dict = {
    "asset_classes": [],
    "instruments": [],
    "companies": [],
    "institutions": [],
    "regions": [],
    "market_layer": "unclear",
    "blockchain_relation": "unclear",
    "tokenization": False,
    "tokenized_asset": "",
    "stablecoin_relation": False,
    "stablecoin_or_digital_money": "",
    "adoption_stage": "unclear",
    "financial_relevance": "low",
    "research_relevance": "low",
    "price_driver": "none",
    "market_sentiment": "unclear",
    "time_horizon": "unclear",
    "confidence_score": 0.2,
    "why_it_matters": "Classificacao falhou.",
    "investment_note": "",
    "red_flags": ["json_parse_error"],
}


def classify(title: str, text: str) -> dict:
    user_prompt = f"""\
Title: {title}

Text:
{text[:settings.max_article_chars]}

Return JSON with EXACTLY these keys:
asset_classes (list: oil | gas_lng | power | renewables | carbon | blockchain_energy | macro_finance),
instruments (list of SPECIFIC tradeable instruments: e.g. "Brent crude futures", "TTF spot", "EUA Dec-25", "Shell equity", "green bond"),
companies (list of company names),
institutions (list of regulatory bodies / exchanges / organisations),
regions (list),
market_layer (string: front_office_trading | exchange_execution | otc_execution | clearing | post_trade | settlement | custody | registry | trade_finance | reporting | risk_management | unclear),
blockchain_relation (string),
tokenization (boolean),
tokenized_asset (string),
stablecoin_relation (boolean),
stablecoin_or_digital_money (string),
adoption_stage (string: concept | pilot | commercial | production | regulated | unclear),
financial_relevance (string: low | medium | high),
research_relevance (string: low | medium | high),
price_driver (string: supply | demand | geopolitical | regulatory | financial | corporate | none),
market_sentiment (string: bullish | bearish | neutral | mixed | unclear),
time_horizon (string: immediate | short_term | medium_term | long_term | unclear),
confidence_score (float 0-1),
why_it_matters (string: 1 sentence on market significance for investors),
investment_note (string: 1 sentence on investment implication, or empty string),
red_flags (list of strings).
"""
    raw = llm.complete(SYSTEM_PROMPT, user_prompt, json_mode=True)
    try:
        result = json.loads(raw)
        result["blockchain_relation"] = _normalise(
            result.get("blockchain_relation", "unclear"), _VALID_BLOCKCHAIN, _BLOCKCHAIN_MAP
        )
        result["price_driver"] = _normalise(
            result.get("price_driver", "none"), _VALID_PRICE_DRIVER
        )
        result["market_sentiment"] = _normalise(
            result.get("market_sentiment", "unclear"), _VALID_SENTIMENT
        )
        result["time_horizon"] = _normalise(
            result.get("time_horizon", "unclear"), _VALID_HORIZON
        )
        return result
    except Exception:
        fallback = dict(_FALLBACK)
        fallback["red_flags"] = ["json_parse_error", raw[:300]]
        return fallback
