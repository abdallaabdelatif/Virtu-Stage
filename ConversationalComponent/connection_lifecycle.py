from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import Any


async def run_until_first_completes(*awaitables: Awaitable[Any]) -> None:
    """Run connection workers and always cancel the workers left behind."""
    tasks = [asyncio.create_task(awaitable) for awaitable in awaitables]
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            task.result()
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
