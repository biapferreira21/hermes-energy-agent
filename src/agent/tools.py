import json

from agents import function_tool

from src.collectors.rss_collector import collect_rss_items
from src.collectors.web_collector import extract_article_text
from src.db import SessionLocal, init_db
from src.models import ResearchItem
from src.processing.clean import clean_text
from src.processing.classify import classify
from src.processing.dedupe import similar_title_exists, url_exists
from src.processing.score import score_item
from src.processing.summarize import summarize
from src.settings import settings


@function_tool
def collect_latest_rss(max_items: int = 30) -> str:
    """Recolhe os artigos mais recentes de todos os feeds RSS configurados."""
    items = collect_rss_items()[:max_items]
    return json.dumps(items, ensure_ascii=False)


@function_tool
def scrape_url(url: str) -> str:
    """Extrai o texto legivel de um artigo a partir do seu URL."""
    return extract_article_text(url)


@function_tool
def process_and_store_item(
    title: str, url: str, source: str = "", published_at: str = ""
) -> str:
    """Faz scraping, classifica, resume e guarda um artigo na base de dados.
    Devolve uma mensagem com o resultado.
    """
    init_db()
    session = SessionLocal()
    try:
        if url_exists(session, url):
            return "Ignorado: URL ja existe na base de dados."
        if similar_title_exists(session, title):
            return "Ignorado: titulo semelhante ja existe."

        raw = extract_article_text(url)
        clean = clean_text(raw or "")

        if len(clean) < settings.min_article_chars:
            # Se nao conseguiu extrair texto suficiente, tenta o summary do RSS
            return f"Ignorado: texto insuficiente ({len(clean)} chars)."

        c = classify(title, clean)
        memo = summarize(title, clean, c)
        signal = score_item(c)

        item = ResearchItem(
            title=title,
            url=url,
            source=source,
            published_at=published_at,
            raw_text=raw,
            clean_text=clean,
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
            confidence_score=float(c.get("confidence_score", 0.5) or 0.5),
            signal_score=float(signal),
            classification_json=json.dumps(c, ensure_ascii=False),
        )
        session.add(item)
        session.commit()
        return (
            f"Guardado id={item.id} | score={signal} | "
            f"blockchain={item.blockchain_relation} | titulo: {title[:60]}"
        )
    finally:
        session.close()


@function_tool
def query_research_database(
    search_term: str = "", min_score: int = 0, limit: int = 20
) -> str:
    """Consulta artigos guardados na base de dados.
    Podes filtrar por texto (search_term) e score minimo.
    """
    init_db()
    session = SessionLocal()
    try:
        q = session.query(ResearchItem).filter(
            ResearchItem.signal_score >= min_score
        )
        if search_term:
            like = f"%{search_term}%"
            q = q.filter(
                ResearchItem.title.ilike(like)
                | ResearchItem.summary.ilike(like)
            )
        rows = q.order_by(ResearchItem.id.desc()).limit(limit).all()
        data = [
            {
                "id": r.id,
                "title": r.title,
                "source": r.source,
                "score": r.signal_score,
                "blockchain_relation": r.blockchain_relation,
                "url": r.url,
            }
            for r in rows
        ]
        return json.dumps(data, ensure_ascii=False)
    finally:
        session.close()
