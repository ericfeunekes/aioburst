'''The async module provides an asynchronous limiter to be used with `asyncion`'''
import asyncio
import pendulum as pdl
from pydantic import BaseModel, PrivateAttr, validator


class Sleeper(BaseModel):
    '''A sleeper is a class that can be used to sleep for a given amount of time'''
    time: pdl.DateTime

    @validator('time', pre=True)
    def time_validator(cls, v):
        '''Validate the time is UTC'''
        if v.tzinfo != pdl.timezone('UTC'):
            raise ValueError('Time must be in UTC')
        return v

    async def wait(self) -> None:
        '''Wait until the time is reached'''
        if self.time > pdl.now(tz='UTC'):
            await asyncio.sleep(self.time.timestamp() - pdl.now(tz='UTC').timestamp())

class AIOBurst(BaseModel):
    '''The AIOBurst class is used to limit the number of concurrent tasks'''
    limit: int = 10
    period: float = 1.0
    num_in_progress: int = 0
    num_todo: int = 0

    _lock: asyncio.Lock = PrivateAttr()
    _in_progress: asyncio.Queue = PrivateAttr()
    _sleepers: asyncio.Queue = PrivateAttr()
    _at_limit: bool = PrivateAttr()
    _semaphore: asyncio.Semaphore = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)  
        self._sleepers = asyncio.Queue(maxsize=self.limit)
        self._semaphore = asyncio.Semaphore(self.limit)
        self._lock = asyncio.Lock()
        self._at_limit = False

    def __aenter__(self):
        '''The `__aenter__` method is used to create the context manager

        Steps:
            1. Check if the queue has reached the limit
            2. If the queue has not reached the limit,
            add the task to _todo
            3. If the queue has reached the limit,
            add the task to _todo, take the oldest Sleeper from _in_progress without committing
        '''
        self._semaphore.acquire()
        if self._at_limit:
            with self._lock:
                self.num_in_progress += 1
            return

        sleeper: Sleeper = self._sleepers.get_nowait()
        self.num_todo -= 1
        sleeper.wait()
        self.num_in_progress += 1
        self.num_todo -= 1
        return

    def __aexit__(self, *args):
        '''The `__aexit__` method is used to create the context manager'''

        self._sleepers.put_nowait(
            Sleeper(time=datetime.now(tz=timezone.utc) + timedelta(seconds=self.period))
            )
        with self._lock:
            if self.num_in_progress == self.limit:
                self._at_limit = True
            self.num_in_progress -= 1
        self._semaphore.release()
        return
