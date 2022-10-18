'''The async module provides an asynchronous limiter to be used with `asyncion`'''
import asyncio
from datetime import datetime, timezone
from pydantic import BaseModel, PrivateAttr, validator


class Sleeper(BaseModel):
    time: datetime

    @validator('time', pre=True):
    def time_validator(cls, v):
        if v.tzinfo != timezone.utc:
            raise ValueError('Time must be in UTC')
        return v

    def wait(self):
        return asyncio.sleep(self.time.timestamp() - datetime.now(tz=timezone.utc).timestamp())

class AIOBurst(BaseModel):
    '''The AIOBurst class is used to limit the number of concurrent tasks'''
    limit: int = 10
    period: float = 1.0

    _lock: asyncio.Lock = PrivateAttr()
    _todo: asyncio.Queue = PrivateAttr()
    _in_progress: asyncio.Queue = PrivateAttr()
    _at_limit: bool = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        
        self._todo = asyncio.Queue(maxsize=0)
        self._in_progress = asyncio.Queue(maxsize=self.limit)
        self._lock = asyncio.Lock()
        self._at_limit = False

    def __aenter__(self):
        '''The `__aenter__` method is used to create the context manager
        
        Steps:
            1. Check if the queue has reached the limit
            2. If the queue has not reached the limit, add the task to _todo
        '''
        return

    def __aexit__(self, *args):
        return

