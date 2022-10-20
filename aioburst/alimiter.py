"""The alimiter module provides AIOBurst, to be used to rate limit code with `asyncio`."""
from __future__ import annotations
import asyncio

import pendulum as pdl
from pydantic import BaseModel, PrivateAttr, validator


class Sleeper(BaseModel):
    """A sleeper is a class that can be used to sleep for a given amount of time

    Attributes
    ----------
    time : DateTime
        The time at which you can start again; in other words, sleep until this time.

    Methods
    -------
    wait(self):
        Wait until the time is reached
    """

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

    Create an instance of AIOBurst with the `create` method. This instance can be used as a context manager to rate
    limit "entry" to the code in the context manager.

    Attributes:
        limit: The maximum number of calls that can be made per period. Defaults to 10.
        period: The period over which to keep track of the number of calls, in seconds. Defaults to 1.

    Methods:
        create: Create an instance of AIOBurst.
    """

    limit: int = 10
    period: float = 1.0

    _num_started: int = PrivateAttr(default=0)
    _sleepers: asyncio.Queue[Sleeper] = PrivateAttr()
    _semaphore: asyncio.Semaphore = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._sleepers = asyncio.Queue(maxsize=0)
        self._semaphore = asyncio.Semaphore(self.limit)

    @classmethod
    def create(cls, limit: int = 10, period: float = 1.0):
        """ Creates an instance of AIOBurst

        Args:
            limit: The maximum number of calls that can be made per period. Defaults to 10.
            period: The period over which to keep track of the number of calls, in seconds. Defaults to 1.

        Returns:

        """
        return AIOBurst(limit=limit, period=period)

    async def __aenter__(self):
        """The `__aenter__` method is used to create the context manager"""
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
