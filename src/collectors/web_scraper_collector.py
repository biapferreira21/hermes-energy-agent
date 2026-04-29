"""Recolhe artigos fazendo scrape das paginas das fontes manuais em sources.yaml."""
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml
import lxml.html

from src.collectors.web_collector import HEADERS

CONFIG_PATH = Path("config/sources.yaml")

_SKIP_WORDS = {
    "login", "register", "signup", "contact", "about", "privacy", "terms",
    "cookie", "sitemap", "rss", "feed", "search", "subscribe", "newsletter",
    "careers", "jobs", "advertis", "help", "faq", "support", "legal",
    "disclaimer", "accessibility", "languag", "logout", "profile", "account",
}

_ARTICLE_SIGNALS = [
    "/news/", "/article/", "/articles/", "/press/", "/publication/",
    "/report/", "/reports/", "/blog/", "/insight/", "/insights/",
    "/analysis/", "/release/", "/releases/", "/content/", "/media/",
    "/story/", "/stories/", "/post/", "/posts/", "/update/",
    "/2023/", "/2024/", "/2025/", "/2026/",
    "/en/news", "/en/press", "/en/report",
]


def _is_article_url(href: str, base_domain: str) -> bool:
    try:
        p = urlparse(href)
    except Exception:
        return False
    if p.scheme not in ("http", "https"):
        return False
    if base_domain not in p.netloc:
        return False
    path = p.path.lower()
    if not path or path in ("/", "/en/", "/es/", "/pt/", "/fr/", "/de/"):
        return False
    # Skip navigation/utility paths
    for word in _SKIP_WORDS:
        if word in path:
            return False
    # Accept if any article signal present
    for sig in _ARTICLE_SIGNALS:
        if sig in path:
            return True
    # Accept if path has 3+ segments (e.g. /en/topics/oil/article-name)
    segments = [s for s in path.split("/") if s]
    return len(segments) >= 3


def _scrape_article_links(page_url: str, max_links: int) -> list[dict]:
    try:
        time.sleep(1.0)
        resp = requests.get(page_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as exc:
        print(f"  [WEB] Erro ao aceder {page_url}: {exc}")
        return []

    try:
        doc = lxml.html.fromstring(resp.text)
        doc.make_links_absolute(page_url)
    except Exception:
        return []

    base_domain = urlparse(page_url).netloc.replace("www.", "")
    seen: set[str] = set()
    results: list[dict] = []

    # Prefer links inside <article>, <h2>, <h3> (typically article listings)
    priority_elements = doc.xpath("//article//a[@href] | //h2/a[@href] | //h3/a[@href]")
    all_elements = doc.xpath("//a[@href]")

    for element in priority_elements + all_elements:
        if len(results) >= max_links:
            break
        href = (element.get("href") or "").strip()
        title = element.text_content().strip()
        if not href or href in seen:
            continue
        if len(title) < 20:
            continue
        if not _is_article_url(href, base_domain):
            continue
        seen.add(href)
        results.append({"title": title[:250], "url": href})

    return results


def load_manual_sources() -> list[dict]:
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    manual = cfg.get("manual_sources", {})
    sources = []
    for category, source_list in manual.items():
        for s in source_list:
            s["_category"] = category
            sources.append(s)
    return sources


def collect_manual_source_items(max_per_source: int = 8) -> list[dict]:
    """Faz scrape das paginas de todas as fontes manuais e devolve artigos encontrados."""
    sources = load_manual_sources()
    items: list[dict] = []

    for source in sources:
        name = source.get("name", "")
        url = source.get("url", "")
        if not url:
            continue
        print(f"  [WEB] A recolher {name} ...")
        links = _scrape_article_links(url, max_links=max_per_source)
        for link in links:
            items.append({
                "title": link["title"],
                "url": link["url"],
                "source": name,
                "source_type": source.get("type", source.get("_category", "")),
                "priority": source.get("priority", "medium"),
                "published_at": "",
                "rss_summary": "",
            })
        print(f"    -> {len(links)} links encontrados")

    print(f"\n[WEB] Total fontes manuais: {len(items)} artigos recolhidos")
    return items
