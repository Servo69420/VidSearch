import asyncpg
from app.config import settings

_pool: asyncpg.Pool | None = None


async def connect():
    global _pool
    _pool = await asyncpg.create_pool(settings.DATABASE_URL)


async def disconnect():
    if _pool:
        await _pool.close()


def get_pool() -> asyncpg.Pool:
    return _pool


async def get_db():
    async with _pool.acquire() as connection:
        yield connection
