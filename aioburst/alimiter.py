"""The async module provides an asynchronous limiter to be used with `asyncio`"""
from __future__ import annotations
import asyncio

import pendulum as pdl
from pydantic import BaseModel, PrivateAttr, validator


class Sleeper(BaseModel):
    """A sleeper is a class that can be used to sleep for a given amount of time"""

    time: pdl.DateTime

    @validator("time", pre=True)
    def time_validator(cls, v):
        """Validate the time is UTC"""
        if v.tzinfo != pdl.timezone("UTC"):
            raise ValueError("Time must be in UTC")
        return v

    async def wait(self) -> None:
        """Wait until the time is reached"""
        if self.time > pdl.now(tz="UTC"):
            await asyncio.sleep(self.time.timestamp() - pdl.now(tz="UTC").timestamp())


class AIOBurst(BaseModel):
    """The AIOBurst class is used to limit the number of concurrent tasks

    Use the `create` method to create a new instance


    """

    limit: int = 10
    period: float = 1.0

    _num_started: int = PrivateAttr(default=0)
    _lock: asyncio.Lock = PrivateAttr()
    _sleepers: asyncio.Queue[Sleeper] = PrivateAttr()
    _at_limit: bool = PrivateAttr()
    _semaphore: asyncio.Semaphore = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._sleepers = asyncio.Queue(maxsize=0)
        self._semaphore = asyncio.Semaphore(self.limit)
        self._lock = asyncio.Lock()
        self._at_limit = False

    @classmethod
    def create(cls, limit: int, period: float):
        """Create an AIOBurst instance

        Parameters
        ----------
        limit
        period

        Returns
        -------

        """
        return AIOBurst(limit=limit, period=period)

    async def __aenter__(self):
        """The `__aenter__` method is used to create the context manager

        Steps:
            1. Check if the queue has reached the limit
            2. If the queue has not reached the limit,
            add the task to _todo
            3. If the queue has reached the limit,
            add the task to _todo, take the oldest Sleeper from _in_progress without committing
        """

        await self._semaphore.acquire()
        if self._num_started < self.limit:
            self._num_started += 1
            return
        try:
            sleeper = self._sleepers.get_nowait()
            self._sleepers.task_done()
            await sleeper.wait()
        except asyncio.QueueEmpty:
            pass
        return

    async def __aexit__(self, *args):
        """The `__aexit__` method is used to create the context manager"""

        self._sleepers.put_nowait(
            Sleeper(time=pdl.now(tz="UTC") + pdl.duration(seconds=self.period))
        )

        self._semaphore.release()
        return
