'''The async module provides an asynchronous limiter to be used with `asyncion`'''
import asyncio
from contextlib import asynccontextmanager
from typing import Union

@asynccontextmanager
async def aioburst(semaphore: asyncio.Semaphore, period: Union[int, float]):
    """Limits the number of calls that can be made within a certain period.

    The semaphore ensures that only that number of calls can be made simultaneously. 
    Before exiting the context manager, the function waits (asynchonous) for `period`,
    this ensures that the correct number of calls are made within the period, regardless
    of when each call returns. 

    Note that the timing is based on when the wrapped function returns. So if you are allowed
    5 calls per second, and 4 return quickly while 1 takes 3 seconds to return, you will be
    able to burst up to 4 calls in seconds 2 and 3 (while waiting for the delayed call to return).

    If you want to limit your function to 5 calls/second, pass in asyncio.Semaphore(5) and set
    period equal to 1.

    If you set period equal to 0 then you'll simply limit the number of simultaneous calls without
    any delay.

    Parameters
    ----------
    semaphore : asyncio.Semaphore
        A semaphore that is instantiated with the number of calls per period.
    period : int | float
        The period over which the number of calls are evaluated.

    Raises
    ------
    TypeError
        The Semaphore must be an asyncio intance. Period must be an int or float
    ValueError
        Period must be greater than 0.
    """    
    if not isinstance(semaphore, asyncio.Semaphore):
        raise TypeError(f'semaphare must be an `asyncio.Semaphore`. You passed in a {type(semaphore)}')
    if type(period) not in (int, float):
        raise TypeError(f'period must be an int or float')
    if period < 0:
        raise ValueError('The `period` must be equal to or greater than 0')
    async with semaphore:
        try:
            yield
        finally:
            await asyncio.sleep(period)
            