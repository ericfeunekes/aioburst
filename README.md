# aioburst
A library to optimize the speed of rate limited async calls, by alternating between bursts and sleeps.

## Usage

Install the package using pip:

`pip install aioburst`

Import the limiter:

`from aioburst import aioburst`

Instantiate the limiter using the `create` method, setting the `limit` (number of calls) and `period` (period over 
which the number of calls are restricted):

```
limiter = AIOBurst.create(limit=10, period=1.0)

async with limiter:
    ...
```
<!-- #TODO: Add Graph showing how this works-->

The code above would allow 10 asynchronous entries (into the context manager) without any limit. Then it adds 
"sleepers" for the next calls. The sleeper tells the next entry when it can start. The 11th call gets the sleeper 
set by the 1st call that returned and waits until the `period` has elapsed. This approach ensures that there are
never more than `limit` simultaneous calls but that the next call can start as soon as possible. The result is that 
in a sliding window of `period` you should see exactly `limit` calls as active, regardless of how fast or slow any 
individual call returns. 

You can also stack limiters:

```
limiter1 = AIOBurst.create(limit=10, period=1.0)
limiter2 = AIOBurst.create(limit=100, period=60.0)

async with limiter1:
	async with limiter2:
    ...
```

<!-- #TODO: Add Graph showing how this works-->

Use this for cases where an API has a two-level rate limit like 10 calls per second or 100 calls per minute---both 
limits will be respected. The stack is also idempotent, meaning that whichever way you stack the limiters, both 
limits will be respected:

```
limiter1 = AIOBurst.create(limit=10, period=1.0)
limiter2 = AIOBurst.create(limit=100, period=60.0)


async with limiter1:
	async with limiter2:
    ...
    
# The limit above will do the exact same thing as the limit below
async with limiter2:
	async with limiter1:
    ...
```

<!-- #TODO: Add Graph showing how this works-->