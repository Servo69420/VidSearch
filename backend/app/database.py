from abc import ABC, abstractmethod

import asyncpg

from app.config import settings
from app.migrations import ensure_admin_setup, ensure_embedding_dimensions


class BaseDatabase(ABC):
    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    def get_pool(self) -> asyncpg.Pool:
        pass


class PostgresDatabase(BaseDatabase):
    def __init__(self, url: str) -> None:
        self.__url: str = url
        self.__pool: asyncpg.Pool | None = None

    @property
    def pool(self) -> asyncpg.Pool | None:
        return self.__pool

    async def connect(self) -> None:
        self.__pool = await asyncpg.create_pool(self.__url)
        async with self.__pool.acquire() as connection:
            await ensure_embedding_dimensions(connection)
            await ensure_admin_setup(connection)

    async def disconnect(self) -> None:
        if self.__pool:
            await self.__pool.close()
            self.__pool = None

    def get_pool(self) -> asyncpg.Pool:
        if self.__pool is None:
            raise RuntimeError(
                "Database pool is not initialised. Call connect() first."
            )
        return self.__pool


_db = PostgresDatabase(settings.DATABASE_URL)


async def connect() -> None:
    await _db.connect()


async def disconnect() -> None:
    await _db.disconnect()


def get_pool() -> asyncpg.Pool:
    return _db.get_pool()


async def get_db():
    async with _db.get_pool().acquire() as connection:
        yield connection
