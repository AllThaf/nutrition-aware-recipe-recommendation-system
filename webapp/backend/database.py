import asyncpg
from typing import AsyncGenerator
from webapp.backend.settings import settings

db_pool = None

async def create_db_pool() -> asyncpg.Pool:
    global db_pool
    if db_pool is None:
        print("Initializing asyncpg connection pool...")
        db_pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60.0
        )
    return db_pool

async def close_db_pool():
    global db_pool
    if db_pool is not None:
        print("Closing asyncpg connection pool...")
        await db_pool.close()
        db_pool = None

async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    global db_pool
    if db_pool is None:
        raise RuntimeError("Database pool has not been initialized. Call create_db_pool() first.")
    
    # Acquire a connection from the pool
    async with db_pool.acquire() as connection:
        yield connection
