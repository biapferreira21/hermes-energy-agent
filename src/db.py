import platform
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.settings import settings

_db_url = settings.database_url

if _db_url.startswith("sqlite:///") and not _db_url.startswith("sqlite:////"):
    _rel = _db_url.replace("sqlite:///", "")
    _src = Path(__file__).parent.parent / _rel

    if platform.system() != "Windows":
        # Streamlit Cloud has a read-only repo filesystem — copy DB to /tmp
        _dst = Path("/tmp/hermes_energy.db")
        try:
            if _src.exists():
                shutil.copy2(_src, _dst)  # always overwrite with latest from repo
        except Exception:
            pass
        _path = _dst if _dst.exists() else _src
    else:
        _path = _src

    _db_url = f"sqlite:///{_path.as_posix()}"

_connect_args = {"check_same_thread": False} if _db_url.startswith("sqlite") else {}
engine = create_engine(_db_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db() -> None:
    from src.models import ResearchItem  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _migrate_new_columns()


def _migrate_new_columns() -> None:
    from sqlalchemy import text
    new_cols = [
        "price_driver TEXT",
        "market_sentiment TEXT",
        "time_horizon TEXT",
    ]
    with engine.connect() as conn:
        for col_def in new_cols:
            try:
                conn.execute(text(f"ALTER TABLE research_items ADD COLUMN {col_def}"))
                conn.commit()
            except Exception:
                pass
