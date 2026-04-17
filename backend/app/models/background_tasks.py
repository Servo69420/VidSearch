"""Background tasks — demonstrates Abstraction, Inheritance, and Polymorphism.

Abstraction:  BackgroundTask defines the interface via ABC.
Inheritance:  TokenCleanupTask extends BackgroundTask.
Polymorphism: TokenCleanupTask overrides the abstract `execute()` method.
"""

import asyncio
import logging
from abc import ABC, abstractmethod

from app.database import get_pool

logger = logging.getLogger(__name__)


class BackgroundTask(ABC):
    """Abstract base for recurring background tasks."""

    def __init__(self, interval_seconds: int) -> None:
        self._interval = interval_seconds

    @abstractmethod
    async def execute(self) -> None:
        """Run one iteration of the task. Subclasses must override."""
        ...

    async def run_forever(self) -> None:
        """Loop: sleep, then execute. Runs until cancelled."""
        while True:
            await asyncio.sleep(self._interval)
            try:
                await self.execute()
            except Exception:
                logger.exception("%s failed", self.__class__.__name__)


class TokenCleanupTask(BackgroundTask):
    """Deletes expired tokens from the blacklist on a schedule."""

    def __init__(self, interval_seconds: int = 3600) -> None:
        super().__init__(interval_seconds)

    async def execute(self) -> None:
        pool = get_pool()
        async with pool.acquire() as conn:
            deleted = await conn.execute(
                "DELETE FROM token_blacklist WHERE expires_at < now()"
            )
            logger.info("Token blacklist cleanup: %s", deleted)
