# aioburst
A library to limit async calls using a waterwheel approach to ensure calls maximize the rate limit. The library is extremely light, using only core python packages.

## Usage

Install the package using pip:

`pip install aioburst`

Import the limiter:

`from aioburst import aioburst`

The package is purely functional, so there is no class to instantiate. `aioburst` is used as a context manager:

```
async with aioburst(semaphore, period):
    ...
```

`semaphore` is an instance of `asyncio.Semaphore` instantiated with a value equal to the number of simultanous calls that are allowed. Pass the `semaphore` instance to `aioburst`. `period` is the period over which the number of calls are evaluated in seconds. For example, if you want to make 4 calls/second, you would pass in `semaphore=Semaphore(4)` and `period=1`.


