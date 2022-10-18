'''Testing alimiter module'''

import asyncio
from asyncio import Semaphore
from typing import Dict, Union

import pendulum as pdl

import numpy as np #type:ignore
import pytest #type:ignore

from aioburst.alimiter import AIOBurst, Sleeper

class TestSleeper:
    '''Tests the Sleeper class'''
    def test_time_validator(self):
        '''Tests the time validator'''
        with pytest.raises(ValueError):
            Sleeper(time=pdl.now(tz='US/Eastern'))

    @pytest.mark.asyncio
    async def test_wait(self):
        '''Tests the wait method'''
        wait_time = 0.5
        sleeper = Sleeper(time=pdl.now(tz='UTC').add(seconds=wait_time))
        started= pdl.now(tz='UTC')
        await sleeper.wait()
        ended = pdl.now(tz='UTC')

        assert ended - started >= pdl.duration(seconds=wait_time)

async def dummy_caller(call_num: int, limiter) -> Dict[str, Union[int, pdl.DateTime]]:
    '''Sends back the time that the function was called.

    If `call_num` is included, it sends back `call_num` with `time`, otherwise
    it just returns `time`.

    Parameters
    ----------
    call_num : int | None, optional
        allows you to track which call is returned, when, by default None

    Returns
    -------
    Dict[str, int | pdl.DateTime]
        a dictionary of the `time` and `call_num` (if provided)
    '''
    async with limiter:
        resp: Dict[str, int | pdl.DateTime] = {'time': pdl.now(tz='UTC')}
        if call_num is not None:
            resp['call_num'] = call_num
        return resp

class TestAIOBurst:
    

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
    with pytest.raises(TypeError):
        semaphore = threading.Semaphore(1)
        async with aioburst(semaphore, 2):
            pass

# @pytest.mark.asyncio
# async def test_wrong_semaphore_value():
#     '''Ensure ValueError is returned if the period is less than 0'''
#     with pytest.raises(ValueError):
#         async with aioburst(asyncio.Semaphore(0), 1):
#             pass

@pytest.mark.asyncio
async def test_wrong_period_type():
    '''Ensure TypeError is returned if period is not a float or int'''
    with pytest.raises(TypeError):
        async with aioburst(asyncio.Semaphore(1), 'wrong'):
            pass

@pytest.mark.asyncio
async def test_wrong_period_value():
    '''Ensure ValueError is returned if the period is less than 0'''
    with pytest.raises(ValueError):
        async with aioburst(asyncio.Semaphore(1), -1):
            pass

#TODO: Use these after you've mocked asyncio sleep so that they don't take forever
# @pytest.mark.asyncio
# @given(s=integers(min_value=1), i=integers(min_value=0, max_value=5))
# async def test_integer_hypothesis(s, i):
#     '''Test aioburst with a range of integers'''
#     async with aioburst(asyncio.Semaphore(s), i):
#         assert True

# @pytest.mark.asyncio
# @given(i=floats(min_value=0, max_value=5))
# async def test_float_hypothesis(i):
#     '''Test aioburst with a range of floats'''
#     async with aioburst(asyncio.Semaphore(), i):
#         assert True