import asyncio
import random
from typing import Any, Awaitable, Callable, Iterable, Type


async def retry_async(
    func: Callable[[], Awaitable[Any]],
    *,
    retries: int = 2,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    retry_exceptions: Iterable[Type[BaseException]] = (Exception,),
) -> Any:
    attempt = 0
    while True:
        try:
            return await func()
        except tuple(retry_exceptions) as exc:
            if attempt >= retries:
                raise
            delay = min(max_delay, base_delay * (2**attempt))
            delay = delay * (0.8 + 0.4 * random.random())
            attempt += 1
            await asyncio.sleep(delay)

