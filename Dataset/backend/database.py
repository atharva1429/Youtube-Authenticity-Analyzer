from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'app.db'}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_columns():
    inspector = inspect(engine)
    if "analysis_history" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("analysis_history")}
    migrations = [
        ("prediction_strength", "VARCHAR(20)"),
        ("decision_score", "FLOAT"),
        ("indicators", "TEXT"),
        ("full_content", "TEXT"),
        ("video_title", "VARCHAR(500)"),
    ]

    with engine.begin() as conn:
        for column, col_type in migrations:
            if column not in existing:
                conn.execute(text(f"ALTER TABLE analysis_history ADD COLUMN {column} {col_type}"))


def init_db():
    from backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_columns()
