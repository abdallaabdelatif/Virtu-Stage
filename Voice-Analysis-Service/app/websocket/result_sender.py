from __future__ import annotations
import asyncio
import json
import logging
from typing import Any
from urllib import error, request


logger = logging.getLogger(__name__)


# assigned the blocking http request to a background thread so as to not to block the event loop
async def post_result(
    callback_url: str,
    payload: dict[str, Any],
    timeout_sec: float = 10.0,
) -> bool:
    return await asyncio.to_thread(
        _post_result_sync,
        callback_url,
        payload,
        timeout_sec,
    )


def _post_result_sync(
    callback_url: str,
    payload: dict[str, Any],
    timeout_sec: float,
) -> bool:
    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        callback_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=timeout_sec) as response:
            status = int(response.status)
            if 200 <= status < 300:
                logger.info("Posted analysis result to %s", callback_url)
                return True

            logger.warning(
                "Result callback returned status %s for %s",
                status,
                callback_url,
            )
            return False
    except (error.URLError, TimeoutError, OSError) as exc:
        logger.warning("Failed to post analysis result to %s: %s", callback_url, exc)
        return False
