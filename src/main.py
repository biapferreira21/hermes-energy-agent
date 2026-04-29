"""Pipeline simples (sem agente): recolhe RSS -> classifica -> guarda -> imprime.
Corre com: python -m src.main
"""
import json
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

from src.collectors.rss_collector import collect_rss_items
from src.collectors.web_scraper_collector import collect_manual_source_items
from src.collectors.web_collector import extract_article_text
from src.db import SessionLocal, init_db
from src.models import ResearchItem
from src.processing.clean import clean_text
from src.processing.classify import classify
from src.processing.dedupe import similar_title_exists, url_exists
from src.processing.score import score_item
from src.processing.summarize import summarize
from src.settings import settings

MAX_AGE_DAYS = 30


def _is_too_old(published_at: str) -> bool:
    """Devolve True se o artigo foi publicado ha mais de MAX_AGE_DAYS dias."""
    if not published_at:
        return False  # sem data -> aceita (nao sabemos)
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    for parser in (parsedate_to_datetime, lambda s: datetime.fromisoformat(s)):
        try:
            dt = parser(published_at)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt < cutoff
        except Exception:
            continue
    return False  # nao conseguiu fazer parse -> aceita


def run_pipeline(max_per_feed: int = 15, max_per_manual: int = 8) -> None:
    """Corre o pipeline completo: recolha RSS + fontes manuais -> classifica -> guarda.

    max_per_feed: maximo de artigos por feed RSS (default 15).
    max_per_manual: maximo de artigos por fonte manual (default 8).
    """
    init_db()
    session = SessionLocal()
    try:
        rss_items = collect_rss_items(max_per_feed=max_per_feed)
        manual_items = collect_manual_source_items(max_per_source=max_per_manual)
        items = rss_items + manual_items
        print(f"\nTotal recolhido: {len(items)} artigos ({len(rss_items)} RSS + {len(manual_items)} fontes manuais).")

        stored = 0
        skipped = 0
        too_old = 0
        for item in items:
            # Filtrar artigos com mais de 30 dias
            if _is_too_old(item.get("published_at", "")):
                too_old += 1
                continue

            # Verificar duplicados antes de fazer scraping (poupa tempo e dinheiro)
            if url_exists(session, item["url"]):
                skipped += 1
                continue
            if similar_title_exists(session, item["title"]):
                skipped += 1
                continue

            # Extrair texto do artigo
            raw = extract_article_text(item["url"])
            text = clean_text(raw or item.get("rss_summary", ""))

            if len(text) < settings.min_article_chars:
                skipped += 1
                continue

            # Classificar e resumir com LLM
            print(f"  A processar: {item['title'][:60]}...")
            c = classify(item["title"], text)
            memo = summarize(item["title"], text, c)
            signal = score_item(c, source_priority=item.get("priority", "medium"))

            row = ResearchItem(
                title=item["title"],
                url=item["url"],
                source=item.get("source"),
                published_at=item.get("published_at"),
                raw_text=raw,
                clean_text=text,
                summary=memo,
                asset_classes=json.dumps(c.get("asset_classes", []), ensure_ascii=False),
                instruments=json.dumps(c.get("instruments", []), ensure_ascii=False),
                companies=json.dumps(c.get("companies", []), ensure_ascii=False),
                institutions=json.dumps(c.get("institutions", []), ensure_ascii=False),
                regions=json.dumps(c.get("regions", []), ensure_ascii=False),
                market_layer=c.get("market_layer"),
                blockchain_relation=c.get("blockchain_relation"),
                tokenization=bool(c.get("tokenization", False)),
                tokenized_asset=c.get("tokenized_asset", ""),
                stablecoin_relation=bool(c.get("stablecoin_relation", False)),
                stablecoin_or_digital_money=c.get("stablecoin_or_digital_money", ""),
                adoption_stage=c.get("adoption_stage"),
                financial_relevance=c.get("financial_relevance"),
                research_relevance=c.get("research_relevance"),
                price_driver=c.get("price_driver"),
                market_sentiment=c.get("market_sentiment"),
                time_horizon=c.get("time_horizon"),
                confidence_score=float(c.get("confidence_score", 0.5) or 0.5),
                signal_score=float(signal),
                classification_json=json.dumps(c, ensure_ascii=False),
            )
            session.add(row)
            try:
                session.commit()
                stored += 1
                print(f"    Guardado id={row.id} | score={signal} | blockchain={row.blockchain_relation}")
            except Exception:
                session.rollback()
                skipped += 1

        print(f"\nPipeline concluido: {stored} guardados, {skipped} ignorados, {too_old} demasiado antigos (>30 dias).")
    finally:
        session.close()


if __name__ == "__main__":
    run_pipeline(max_per_feed=15)
