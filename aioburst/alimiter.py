'''The async module provides an asynchronous limiter to be used with `asyncion`'''
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def aioburst(semaphore: asyncio.Semaphore, period: int):
    '''Limits the number of calls that can be made within a certain period.
    '''
    async with semaphore:
        try:
            yield
        finally:
            await asyncio.sleep(period)
            