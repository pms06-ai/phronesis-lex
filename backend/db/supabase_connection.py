"""
Supabase Database Connection
PostgreSQL connection with async support via asyncpg
"""
import os
import json
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import asyncpg
from datetime import datetime, date
import uuid

# Get Supabase connection string from environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # anon or service_role key
DATABASE_URL = os.getenv("DATABASE_URL", "")  # Direct PostgreSQL connection string


class SupabaseDB:
    """PostgreSQL database manager for Supabase with async support"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._connection_string = DATABASE_URL

    async def connect(self):
        """Create connection pool"""
        if not self._connection_string:
            raise ValueError(
                "DATABASE_URL not set. Get it from Supabase Dashboard > Settings > Database > Connection string"
            )

        self.pool = await asyncpg.create_pool(
            self._connection_string,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        return self.pool

    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def initialize(self):
        """Verify database connection (schema should be created via Supabase SQL editor)"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            # Verify tables exist
            result = await conn.fetchval(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
            print(f"Supabase connected. Found {result} tables.")

    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch a single row as dictionary"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch all rows as list of dictionaries"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def execute(self, query: str, *args):
        """Execute a query"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def insert(self, table: str, data: Dict[str, Any]) -> str:
        """Insert a row and return the ID"""
        # Generate UUID if not provided
        if "id" not in data:
            data["id"] = str(uuid.uuid4())

        # Convert Python types to PostgreSQL compatible
        processed_data = self._process_data(data)

        columns = ", ".join(processed_data.keys())
        placeholders = ", ".join([f"${i+1}" for i in range(len(processed_data))])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"

        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            result = await conn.fetchval(query, *processed_data.values())
            return str(result)

    async def update(self, table: str, id: str, data: Dict[str, Any]):
        """Update a row by ID"""
        processed_data = self._process_data(data)

        set_parts = [f"{k} = ${i+1}" for i, k in enumerate(processed_data.keys())]
        set_clause = ", ".join(set_parts)
        query = f"UPDATE {table} SET {set_clause} WHERE id = ${len(processed_data)+1}"

        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            await conn.execute(query, *processed_data.values(), uuid.UUID(id))

    async def delete(self, table: str, id: str):
        """Delete a row by ID"""
        query = f"DELETE FROM {table} WHERE id = $1"

        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            await conn.execute(query, uuid.UUID(id))

    def _process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data for PostgreSQL compatibility"""
        processed = {}
        for key, value in data.items():
            if isinstance(value, dict) or isinstance(value, list):
                # Convert to JSON string for JSONB columns
                processed[key] = json.dumps(value)
            elif isinstance(value, str) and self._is_uuid(value):
                # Convert UUID strings to UUID objects
                processed[key] = uuid.UUID(value)
            else:
                processed[key] = value
        return processed

    def _is_uuid(self, value: str) -> bool:
        """Check if string is a valid UUID"""
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            return False


# Global database instance
db = SupabaseDB()


async def get_db() -> SupabaseDB:
    """Dependency injection for FastAPI"""
    return db
