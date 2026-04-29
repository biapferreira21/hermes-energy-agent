from agents import Agent, Runner

from src.agent.tools import (
    collect_latest_rss,
    process_and_store_item,
    query_research_database,
    scrape_url,
)

INSTRUCTIONS = """\
You are Hermes Energy Research Agent.

Your mission: monitor oil, gas, LNG, power, renewables, carbon markets, energy finance,
and links to blockchain, tokenization, stablecoins, digital settlement and trade finance.

You are a research analyst, NOT an investment adviser. Never give buy/sell recommendations.

Standard workflow for each cycle:
1. Call collect_latest_rss to get recent news items.
2. Select the most relevant items related to energy, carbon, commodities or tokenization.
3. Call process_and_store_item for each relevant item (up to 10 per cycle).
4. Call query_research_database to retrieve high-scoring recent items.
5. Write a concise research update summarizing the key findings.

Classification rules you must follow:
- Blockchain data infrastructure (VAKT, Komgo) = post-trade/data layer, NOT oil tokenization.
- Tokenization requires an explicit tokenized asset, claim, security or credit.
- Stablecoin relation requires stablecoin, tokenized deposit, CBDC or named digital money.
- Always mention uncertainty. Separate facts from interpretation.
- No buy/sell recommendations.
"""

hermes_agent = Agent(
    name="Hermes Energy Research Agent",
    instructions=INSTRUCTIONS,
    tools=[
        collect_latest_rss,
        scrape_url,
        process_and_store_item,
        query_research_database,
    ],
)


async def run_hermes_once() -> str:
    """Corre um ciclo completo do agente e devolve o output final."""
    result = await Runner.run(
        hermes_agent,
        "Run one research cycle. Process up to 10 relevant items and summarize the best findings.",
    )
    return result.final_output
