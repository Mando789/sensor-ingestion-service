"""
Database setup and schema definition

This file handles two things:
1. Connecting to / disconnecting from a SQLite database.
2. Defining the 'sensor_readings' table schema using SQLAlchemy Core.

"""

import sqlalchemy
from databases import Database

# Connection URL
# 'aiosqlite' is the async driver
DATABASE_URL = "sqlite+aiosqlite:///./sensor_data.db"


# Database instance
database = Database(DATABASE_URL)


# SQLAlchemy metadata & table definition

metadata = sqlalchemy.MetaData()

sensor_readings = sqlalchemy.Table(
    "sensor_readings",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("sensor_id", sqlalchemy.String(64), nullable=False, index=True),
    sqlalchemy.Column("timestamp", sqlalchemy.String(64), nullable=False, index=True),
    sqlalchemy.Column("reading", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column(
        "ingested_at",
        sqlalchemy.String(64),
        nullable=False,
        server_default=sqlalchemy.text("(datetime('now'))"),
    ),
)


def create_tables() -> None:
    """
    Create all tables defined in 'metadata' if they do not already exist.

    We use a *synchronous* engine here because this runs once at startup
    before the async event loop takes over.  SQLAlchemy's create_all is
    synchronous; using it this way is the recommended approach in the
    'databases' library documentation.
    """
    # Build a synchronous engine pointing at the same DB file.
    sync_engine = sqlalchemy.create_engine(
        DATABASE_URL.replace("+aiosqlite", ""),  
        connect_args={"check_same_thread": False},
    )
    metadata.create_all(sync_engine)
    sync_engine.dispose()  # Close immediately. We won't use this engine again.