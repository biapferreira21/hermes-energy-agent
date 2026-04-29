from rapidfuzz import fuzz

from src.models import ResearchItem


def url_exists(session, url: str) -> bool:
    """Verifica se o URL ja existe na base de dados."""
    return (
        session.query(ResearchItem)
        .filter(ResearchItem.url == url)
        .first()
        is not None
    )


def similar_title_exists(session, title: str, threshold: int = 92) -> bool:
    """Verifica se ja existe um titulo muito semelhante (evita duplicados com URL diferente)."""
    recent = (
        session.query(ResearchItem)
        .order_by(ResearchItem.id.desc())
        .limit(500)
        .all()
    )
    for item in recent:
        score = fuzz.token_set_ratio(title.lower(), item.title.lower())
        if score >= threshold:
            return True
    return False
