'''Testing alimiter module'''

import asyncio
from asyncio import Semaphore
from datetime import datetime, timezone
from typing import Dict, Union

import numpy as np #type:ignore
import pytest #type:ignore

from aioburst import aioburst

async def call_time(call_num: int, limiter) -> Dict[str, Union[int, datetime]]:
    '''Sends back the time that the function was called.

    If `call_num` is included, it sends back `call_num` with `time`, otherwise
    it just returns `time`.

    Parameters
    ----------
    call_num : int | None, optional
        allows you to track which call is returned, when, by default None

    Returns
    -------
    Dict[str, int | datetime]
        a dictionary of the `time` and `call_num` (if provided)
    '''
    async with limiter:
        resp: Dict[str, int | datetime] = {'time': datetime.now(timezone.utc)}
        if call_num is not None:
            resp['call_num'] = call_num
        return resp

@pytest.mark.asyncio
async def test_limiter():
    '''Test whether the limiter actually burst the correct number of times within the period'''
    max_calls = 4
    period = 2
    sem = Semaphore(max_calls)

    tasks = []
    for i in range(8):
        task = asyncio.create_task(call_time(i, aioburst(sem, period)))
        tasks.append(task)

    done = await asyncio.gather(*tasks)
    times = [d['time'] for d in done]
    seconds = [d['time'].second for d in done]

    # First four values should burst in the same second
    np.testing.assert_array_equal(seconds[:4],[seconds[0]]*4)
    # Last four values should burst in the same second
    np.testing.assert_array_equal(seconds[4:],[seconds[-1]]*4)
    # First value should be 2 times less than the last value
    assert (times[-1] - times[0]).seconds == period

@pytest.mark.asyncio
async def test_wrong_semaphore_type():
    '''Ensure TypeError is returned if the wrong Semaphore is passed in'''
    import threading
    with pytest.raises(TypeError):
        semaphore = threading.Semaphore(1)
        async with aioburst(semaphore, 2):
            pass

@pytest.mark.asyncio
async def test_wrong_period_type():
    with pytest.raises(TypeError):
        async with aioburst(asyncio.Semaphore(1), 'wrong'):
            pass

@pytest.mark.asyncio
async def test_wrong_period_value():
    with pytest.raises(ValueError):
        async with aioburst(asyncio.Semaphore(1), -1):
            pass