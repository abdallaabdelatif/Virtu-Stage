import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from connection_lifecycle import run_until_first_completes  # noqa: E402


def test_cancels_worker_left_after_peer_completes() -> None:
    async def exercise() -> None:
        cancelled = asyncio.Event()

        async def completes() -> None:
            await asyncio.sleep(0)

        async def waits_forever() -> None:
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        await run_until_first_completes(completes(), waits_forever())
        assert cancelled.is_set()

    asyncio.run(exercise())


def test_propagates_worker_error_and_cancels_peer() -> None:
    async def exercise() -> None:
        cancelled = asyncio.Event()

        async def fails() -> None:
            await asyncio.sleep(0)
            raise RuntimeError("worker failed")

        async def waits_forever() -> None:
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        try:
            await run_until_first_completes(fails(), waits_forever())
        except RuntimeError as exc:
            assert str(exc) == "worker failed"
        else:
            raise AssertionError("worker error was not propagated")

        assert cancelled.is_set()

    asyncio.run(exercise())
