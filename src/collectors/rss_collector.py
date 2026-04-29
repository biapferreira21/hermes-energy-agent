import feedparser
import requests
import yaml
from pathlib import Path

CONFIG_PATH = Path("config/sources.yaml")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; HermesEnergyAgent/1.0; "
        "+https://github.com/hermes-energy)"
    )
}


def load_feeds() -> list[dict]:
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return cfg.get("rss_feeds", [])


def _fetch_feed(url: str) -> feedparser.FeedParserDict:
    """Usa requests (com certificados do sistema) para buscar o feed,
    depois passa o conteudo ao feedparser para parse do XML/Atom.
    Isto resolve o problema de proxy/SSL em redes empresariais.
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    except Exception:
        # Fallback: tenta directamente com feedparser (pode falhar no proxy)
        return feedparser.parse(url)


def collect_rss_items(max_per_feed: int = 15) -> list[dict]:
    """Recolhe artigos de TODOS os feeds RSS, com limite por feed."""
    items = []
    for feed_cfg in load_feeds():
        try:
            parsed = _fetch_feed(feed_cfg["url"])
            count = 0
            for entry in parsed.entries:
                if count >= max_per_feed:
                    break
                title = entry.get("title", "").strip()
                url = entry.get("link", "").strip()
                if not title or not url:
                    continue
                items.append({
                    "title": title,
                    "url": url,
                    "source": feed_cfg.get("name"),
                    "source_type": feed_cfg.get("source_type"),
                    "priority": feed_cfg.get("priority"),
                    "published_at": entry.get("published", entry.get("updated", "")),
                    "rss_summary": entry.get("summary", ""),
                })
                count += 1
            print(f"  [RSS] {feed_cfg.get('name')}: {count} artigos recolhidos")
        except Exception as exc:
            print(f"  [RSS] Erro no feed {feed_cfg.get('name')}: {exc}")
    return items
