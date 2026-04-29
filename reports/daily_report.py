"""Gera um relatorio diario em Markdown com os artigos de maior score.
Corre com: python -m reports.daily_report
O ficheiro e guardado em data/reports/hermes_daily_YYYY-MM-DD.md
"""
from datetime import datetime
from pathlib import Path

from src.db import SessionLocal, init_db
from src.models import ResearchItem


def generate_daily_report(limit: int = 25) -> Path:
    init_db()
    session = SessionLocal()
    try:
        rows = (
            session.query(ResearchItem)
            .order_by(ResearchItem.signal_score.desc())
            .limit(limit)
            .all()
        )

        today = datetime.now().strftime("%Y-%m-%d")
        out_path = Path("data/reports") / f"hermes_daily_{today}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# Hermes Energy Daily Report - {today}\n",
            f"_Gerado automaticamente. {len(rows)} artigos de maior score._\n",
            "---\n",
        ]

        for r in rows:
            lines.append(f"## {r.title}")
            lines.append(
                f"**Fonte:** {r.source or 'N/A'} | "
                f"**Score:** {r.signal_score} | "
                f"**Data pub:** {r.published_at or 'N/A'}"
            )
            lines.append(f"**URL:** {r.url}")
            lines.append(
                f"**Blockchain:** `{r.blockchain_relation}` | "
                f"**Tokenizacao:** {r.tokenization} | "
                f"**Stablecoin:** {r.stablecoin_relation} | "
                f"**Relevancia fin:** {r.financial_relevance}"
            )
            lines.append("")
            lines.append(r.summary or "_Sem resumo_")
            lines.append("\n---\n")

        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"Relatorio guardado em: {out_path}")
        return out_path
    finally:
        session.close()


if __name__ == "__main__":
    generate_daily_report()
