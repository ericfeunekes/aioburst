'''The async module provides an asynchronous limiter to be used with `asyncion`'''
import asyncio


async def limiter(semaphore: asyncio.Semaphore, period: int):
    '''Limits the number of calls that can be made within a certain period.
    '''
    async with semaphore:
        try:
            yield
        finally:
            await asyncio.sleep(period)