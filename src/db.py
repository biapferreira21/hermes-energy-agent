from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.settings import settings

# check_same_thread=False so SQLite works with Streamlit
_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db() -> None:
    from src.models import ResearchItem  # noqa: F401 - import to register model
    Base.metadata.create_all(bind=engine)
    _migrate_new_columns()


def _migrate_new_columns() -> None:
    """Adiciona colunas novas a tabelas existentes sem perder dados."""
    from sqlalchemy import text
    new_cols = [
        "price_driver TEXT",
        "market_sentiment TEXT",
        "time_horizon TEXT",
    ]
    with engine.connect() as conn:
        for col_def in new_cols:
            col_name = col_def.split()[0]
            try:
                conn.execute(text(f"ALTER TABLE research_items ADD COLUMN {col_def}"))
                conn.commit()
            except Exception:
                pass  # coluna ja existe
