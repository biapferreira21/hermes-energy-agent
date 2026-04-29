import platform
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.settings import settings

_src = Path(__file__).resolve().parent.parent / "data/hermes_energy.db"

if platform.system() != "Windows" and _src.exists():
    # Streamlit Cloud: open SQLite in immutable read-only mode (no journal files needed)
    _abs = str(_src)
    engine = create_engine(
        "sqlite+pysqlite://",
        creator=lambda: sqlite3.connect(f"file:{_abs}?immutable=1", uri=True, check_same_thread=False),
    )
else:
    _db_url = settings.database_url if not settings.database_url.startswith("sqlite:///data") \
        else f"sqlite:///{_src.as_posix()}"
    engine = create_engine(_db_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db() -> None:
    from src.models import ResearchItem  # noqa: F401
    try:
        Base.metadata.create_all(bind=engine)
        _migrate_new_columns()
    except Exception:
        pass  # read-only on Streamlit Cloud — tables already exist


def _migrate_new_columns() -> None:
    from sqlalchemy import text
    new_cols = ["price_driver TEXT", "market_sentiment TEXT", "time_horizon TEXT"]
    with engine.connect() as conn:
        for col_def in new_cols:
            try:
                conn.execute(text(f"ALTER TABLE research_items ADD COLUMN {col_def}"))
                conn.commit()
            except Exception:
                pass
