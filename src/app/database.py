import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./data/store_intelligence.db')
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(DATABASE_URL, echo=False, connect_args={'check_same_thread': False, 'timeout': 15})
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        conn.execute(text("PRAGMA synchronous=NORMAL;"))
else:
    engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    from .models import Event, VisitorSession, StoreMetric, POSRecord

    if DATABASE_URL.startswith('sqlite'):
        db_path = DATABASE_URL.replace('sqlite:///', '')
        if db_path and not os.path.exists(os.path.dirname(db_path)):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

    SQLModel.metadata.create_all(engine)
    _repair_sqlite_schema()


def _repair_sqlite_schema() -> None:
    if not DATABASE_URL.startswith('sqlite'):
        return

    with engine.begin() as connection:
        for table_name, columns in {
            'visitorsession': [
                ('billing_seen', 'BOOLEAN DEFAULT 0'),
                ('billing_first_seen', 'DATETIME'),
                ('is_converted', 'BOOLEAN DEFAULT 0'),
            ],
            'event': [
                ('metadata', 'JSON'),
            ],
        }.items():
            existing = {
                row['name']
                for row in connection.exec_driver_sql(f"PRAGMA table_info({table_name})").mappings()
            }
            for column_name, column_type in columns:
                if column_name not in existing:
                    connection.exec_driver_sql(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')


def get_session() -> Session:
    return Session(engine)
