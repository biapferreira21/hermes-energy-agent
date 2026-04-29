from src.llm_providers import llm
from src.settings import settings

SYSTEM_PROMPT = """\
You are Hermes Energy Intelligence Analyst.

Write structured investment intelligence memos for an energy markets professional.
The reader manages investments across oil, gas, LNG, power, renewables, carbon markets,
and blockchain/tokenization infrastructure.

Style rules:
- Lead with the market signal, not the story
- Be specific about price, volume, quantity when mentioned in the article
- Identify which players are gaining vs losing positioning
- Separate facts from implications clearly
- Flag uncertainty or missing information
- Write in English regardless of the article language
- Be concise: each section max 2-3 sentences
"""


def summarize(title: str, text: str, classification: dict) -> str:
    sentiment = classification.get("market_sentiment", "unclear")
    driver = classification.get("price_driver", "none")
    horizon = classification.get("time_horizon", "unclear")
    instruments = ", ".join(classification.get("instruments", [])) or "N/A"

    user_prompt = f"""\
Title: {title}
Instruments: {instruments}
Market sentiment: {sentiment} | Price driver: {driver} | Time horizon: {horizon}
Classification: {classification}

Article:
{text[:settings.max_article_chars]}

Write an investment intelligence memo with these 7 sections:

## Signal
One sentence: what is the core market signal (bullish/bearish/neutral) and why.

## Key Players & Moves
Who are the main actors? What position/action are they taking? Who benefits, who loses?

## Asset & Instrument Impact
Which specific instruments are directly affected (e.g. Brent futures, TTF spot, EUA, LNG spot)?
Quantify impact if data is available.

## Supply / Demand / Price Dynamics
What changes in supply, demand, or pricing does this create or reflect?

## Macro & Regulatory Context
Any macro, geopolitical, or regulatory backdrop that amplifies or limits the impact?

## Investment Considerations
What should an investor monitor or analyse further? Any positioning implication?
(Do not give direct buy/sell advice — frame as considerations to evaluate.)

## Risks & Uncertainties
What could make this signal wrong? What information is missing?
"""
    return llm.complete(SYSTEM_PROMPT, user_prompt, json_mode=False)
