import asyncio
from contextlib import suppress

from telegramsales.apps.bot.notifications import run_outbox

SENT = 1
NOTHING = 0
NO_PAUSE = 0.0


class FlakyTick:
    def __init__(self, *results: int | Exception) -> None:
        self.results: list[int | Exception] = list(results)
        self.calls: int = 0
        self.exhausted: asyncio.Event = asyncio.Event()

    async def __call__(self) -> int:
        self.calls += 1
        if not self.results:
            self.exhausted.set()
            await asyncio.sleep(0)
            return NOTHING

        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def worker_for(tick: FlakyTick) -> asyncio.Task[None]:
    return asyncio.create_task(
        run_outbox(tick, idle_pause=NO_PAUSE, failure_pause=NO_PAUSE)
    )


async def drive(tick: FlakyTick) -> None:
    worker = worker_for(tick)
    await asyncio.wait_for(tick.exhausted.wait(), timeout=1)
    worker.cancel()
    with suppress(asyncio.CancelledError):
        await worker


async def test_the_worker_keeps_dispatching_while_there_is_work() -> None:
    tick = FlakyTick(SENT, SENT, SENT)

    await drive(tick)

    assert tick.calls > 3


async def test_a_failed_tick_does_not_stop_the_worker() -> None:
    tick = FlakyTick(RuntimeError("database is away"), SENT)

    await drive(tick)

    assert tick.calls > 2


async def test_the_worker_stops_on_cancel() -> None:
    tick = FlakyTick(SENT)
    worker = worker_for(tick)
    await asyncio.wait_for(tick.exhausted.wait(), timeout=1)

    worker.cancel()
    with suppress(asyncio.CancelledError):
        await worker

    assert worker.done()
