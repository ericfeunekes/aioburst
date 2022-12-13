"""Testing alimiter module"""

import asyncio
from typing import Dict, Union

import pendulum as pdl

import numpy as np  # type:ignore
import pytest  # type:ignore
from hypothesis import given, settings
from hypothesis.strategies import floats, integers

from aioburst.alimiter import AIOBurst, Sleeper


class TestSleeper:
    """Tests the Sleeper class"""

    def test_time_validator(self):
        """Tests the time validator"""
        with pytest.raises(ValueError):
            Sleeper(time=pdl.now(tz="US/Eastern"))

    @pytest.mark.asyncio
    async def test_wait(self):
        """Tests the wait method"""
        wait_time = 0.5
        sleeper = Sleeper(time=pdl.now(tz="UTC").add(seconds=wait_time))
        started = pdl.now(tz="UTC")
        await sleeper.wait()
        ended = pdl.now(tz="UTC")

        assert ended - started >= pdl.duration(seconds=wait_time)


async def dummy_caller(
    call_num: int, limiter: AIOBurst
) -> Dict[str, Union[int, pdl.DateTime]]:
    async with limiter:
        resp: Dict[str, int | pdl.DateTime] = {"time": pdl.now(tz="UTC")}
        if call_num is not None:
            resp["call_num"] = call_num
        return resp


async def dummy_two_limit_caller(
    call_num: int, limiter1: AIOBurst, limiter2: AIOBurst
) -> Dict[str, Union[int, pdl.DateTime]]:
    async with limiter1:
        async with limiter2:
            resp: Dict[str, int | pdl.DateTime] = {"time": pdl.now(tz="UTC")}
            if call_num is not None:
                resp["call_num"] = call_num
    return resp


async def double_limiter_run(
        limiter_high, limiter_low, max_calls_high, max_calls_low, period_high, period_low
):
    '''Helper function to run the double limiter and check output'''
    tasks = []
    for i in range(max_calls_high+1):
        task = asyncio.create_task(
            dummy_two_limit_caller(i, limiter1=limiter_high, limiter2=limiter_low)
        )
        tasks.append(task)
    done = await asyncio.gather(*tasks)
    times = [d["time"] for d in done]
    seconds = [d["time"].second for d in done]
    # Last four values should burst in the same second
    assert (times[-1] - times[0]).seconds == period_high
    assert (times[max_calls_low] - times[0]).seconds == period_low


def test_limiter_simple():
    results = []
    limiter = AIOBurst(max_calls=5, period=1)
    async with limiter: 
        results.append(now())

    print(results)


class TestAIOBurst:
    def test_init(self):
        limiter = AIOBurst.create(limit=10, period=1.0)
        assert limiter.limit == 10
        assert limiter.period == 1.0
        assert limiter._num_started == 0
        assert isinstance(limiter._sleepers, asyncio.Queue)
        assert isinstance(limiter._semaphore, asyncio.Semaphore)

    @pytest.mark.asyncio
    async def test_limiter(self):
        """The limiter should burst twice and those bursts should be `period` seconds apart"""
        max_calls = 4
        period = 2
        limiter = AIOBurst.create(limit=max_calls, period=period)

        tasks = []
        for i in range(8):
            task = asyncio.create_task(dummy_caller(i, limiter))
            tasks.append(task)

        done = await asyncio.gather(*tasks)
        times = [d["time"] for d in done]
        seconds = [d["time"].second for d in done]

        # First four values should burst in the same second
        np.testing.assert_array_equal(seconds[:4], [seconds[0]] * 4)
        # Last four values should burst in the same second
        np.testing.assert_array_equal(seconds[4:], [seconds[-1]] * 4)
        # First value should be 2 times less than the last value
        assert (times[-1] - times[0]).seconds == period

    @pytest.mark.asyncio
    async def test_two_limiters(self):
        """With two limiters the low rate should burst as normal, then when the high limit is reached, the high limiter
        should kick in as well. When they are finished, there should be no additional delay
        """
        max_calls_high = 10
        period_high = 6

        max_calls_low = 3
        period_low = 1
        limiter_low = AIOBurst.create(limit=max_calls_low, period=period_low)
        limiter_high = AIOBurst.create(limit=max_calls_high, period=period_high)

        # The order of limiters should not matter. The results should come back in the same amount of time
        # Run once with the large limit first
        await double_limiter_run(
            limiter_high, limiter_low, max_calls_high, max_calls_low, period_high, period_low
        )
        # Run again with the large limit second
        await double_limiter_run(
            limiter_low, limiter_high, max_calls_high, max_calls_low, period_high, period_low
        )

    # @pytest.mark.slow
    # @pytest.mark.asyncio
    # @settings(max_examples=10)
    # @given(
    #     max_low=integers(min_value=2, max_value=1000),
    #     period_low=floats(min_value=0, max_value=2),
    #     max_high_mult=floats(min_value=0, max_value=2),
    #     period_high_mult=floats(min_value=0, max_value=2)
    # )
    # async def test_integer_hypothesis(self, max_low, period_low, max_high_mult, period_high_mult):
    #     """Test aioburst with a range of integers"""
    #     max_calls_high = int(max_low * max_high_mult)
    #     period_high = period_low * period_high_mult
    #
    #     max_calls_low = max_low
    #     period_low = period_low
    #     limiter_low = AIOBurst.create(limit=max_calls_low, period=period_low)
    #     limiter_high = AIOBurst.create(limit=max_calls_high, period=period_high)
    #
    #     # The order of limiters should not matter. The results should come back in the same amount of time
    #     # Run once with the large limit first
    #     await double_limiter_run(
    #         limiter_high, limiter_low, max_calls_high, max_calls_low, period_high, period_low
    #     )

