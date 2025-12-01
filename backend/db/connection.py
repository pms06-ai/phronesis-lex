"""
Database Connection Management
SQLite connection with async support via aiosqlite
"""
import sqlite3
import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager
import json

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import DATABASE_PATH, DB_DIR

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def dict_factory(cursor, row):
    """Convert SQLite rows to dictionaries"""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


class Database:
    """SQLite database manager with async support"""

    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self._connection = None

    async def connect(self):
        """Establish database connection"""
        self._connection = await aiosqlite.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA foreign_keys = ON")
        await self._connection.execute("PRAGMA journal_mode = WAL")
        return self._connection

    async def disconnect(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def initialize(self):
        """Initialize database with schema"""
        if not SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

        async with aiosqlite.connect(self.db_path) as db:
            schema = SCHEMA_PATH.read_text()
            await db.executescript(schema)
            await db.commit()

        import logging
        logging.getLogger(__name__).info(f"Database initialized at {self.db_path}")

    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions"""
        conn = await self.connect()
        try:
            yield conn
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            raise e
        finally:
            await self.disconnect()

    async def execute(self, query: str, params: tuple = ()):
        """Execute a single query"""
        async with self.transaction() as conn:
            cursor = await conn.execute(query, params)
            return cursor

    async def fetch_one(self, query: str, params: tuple = ()):
        """Fetch a single row"""
        async with self.transaction() as conn:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def fetch_all(self, query: str, params: tuple = ()):
        """Fetch all rows"""
        async with self.transaction() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def insert(self, table: str, data: dict) -> str:
        """Insert a row and return the ID"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        async with self.transaction() as conn:
            cursor = await conn.execute(query, tuple(data.values()))
            return data.get("id") or cursor.lastrowid

    async def update(self, table: str, id: str, data: dict):
        """Update a row by ID"""
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE id = ?"

        async with self.transaction() as conn:
            await conn.execute(query, (*data.values(), id))

    async def delete(self, table: str, id: str):
        """Delete a row by ID"""
        query = f"DELETE FROM {table} WHERE id = ?"
        async with self.transaction() as conn:
            await conn.execute(query, (id,))

    async def execute_script(self, script: str):
        """Execute a multi-statement SQL script"""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.executescript(script)
            await conn.commit()


# Global database instance
db = Database()


async def get_db() -> Database:
    """Dependency injection for FastAPI"""
    return db


def init_db_sync():
    """Synchronous database initialization for startup"""
    import asyncio
    asyncio.run(db.initialize())


if __name__ == "__main__":
    # Initialize database when run directly
    import logging
    logging.basicConfig(level=logging.INFO)
    init_db_sync()
    logging.getLogger(__name__).info("Database setup complete!")
