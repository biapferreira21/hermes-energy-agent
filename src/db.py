import platform
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.settings import settings

_db_url = settings.database_url
_src = Path(__file__).resolve().parent.parent / "data/hermes_energy.db"
_copy_error = ""

if _db_url.startswith("sqlite:///") and not _db_url.startswith("sqlite:////"):
    if platform.system() != "Windows":
        _dst = Path("/tmp/hermes_energy.db")
        try:
            if _src.exists():
                _dst.write_bytes(_src.read_bytes())
        except Exception as e:
            _copy_error = str(e)
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
