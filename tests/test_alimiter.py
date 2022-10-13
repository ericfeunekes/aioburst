from datetime import datetime, timezone
from typing import List, Dict
import pandas as pd
import pytest

def call_time(call_num: int | None = None) -> Dict[str, int | datetime]:
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
    d = {'call_num': call_num} if call_num is None else {}
    d['time'] = datetime.now(timezone.utc)
    return d



