"""
SASTRA Research Finder - Database Connection
SQLAlchemy engine and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.SQLALCHEMY_DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _sqlite_column_type(col) -> str:
    """Render a SQLAlchemy column type to a SQLite-compatible DDL fragment."""
    try:
        compiled = col.type.compile(dialect=engine.dialect)
    except Exception:
        compiled = "TEXT"
    return compiled or "TEXT"


def _auto_migrate_sqlite(Base):
    """Add any columns declared on ORM models that are missing from existing SQLite tables.

    create_all() never alters existing tables, so when we add fields to db_models.py
    the table schema drifts. This helper patches that drift for SQLite only — good
    enough for the dev/embedded DB this project uses.
    """
    if "sqlite" not in settings.SQLALCHEMY_DATABASE_URL:
        return
    from sqlalchemy import text

    inspector_sql = "SELECT name FROM sqlite_master WHERE type='table'"
    with engine.connect() as conn:
        existing_tables = {r[0] for r in conn.execute(text(inspector_sql))}

        for table_name, table in Base.metadata.tables.items():
            if table_name not in existing_tables:
                continue

            cols_in_db = {
                row[1] for row in conn.execute(text(f"PRAGMA table_info('{table_name}')"))
            }
            for col in table.columns:
                if col.name in cols_in_db:
                    continue
                col_type = _sqlite_column_type(col)
                default_clause = ""
                if col.default is not None and getattr(col.default, "is_scalar", False):
                    val = col.default.arg
                    if isinstance(val, bool):
                        default_clause = f" DEFAULT {1 if val else 0}"
                    elif isinstance(val, (int, float)):
                        default_clause = f" DEFAULT {val}"
                    elif isinstance(val, str):
                        safe = val.replace("'", "''")
                        default_clause = f" DEFAULT '{safe}'"
                stmt = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_clause}"
                try:
                    conn.execute(text(stmt))
                    print(f"  ✓ migrated: {table_name} + {col.name} ({col_type})")
                except Exception as e:
                    print(f"  ⚠️ could not add column {table_name}.{col.name}: {e}")
        conn.commit()


def init_db():
    """Initialize database tables. Creates missing tables and migrates missing columns."""
    from app.models.db_models import Base
    Base.metadata.create_all(bind=engine)
    _auto_migrate_sqlite(Base)