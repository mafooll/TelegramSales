import time
from typing import Any

from sqlalchemy import Connection, event
from sqlalchemy.engine.interfaces import ExecutionContext
from sqlalchemy.ext.asyncio import AsyncEngine
import structlog
from structlog.stdlib import BoundLogger

logger: BoundLogger = structlog.get_logger()

MILLISECONDS = 1000
STARTED_KEY = "telegramsales_started_at"
MAX_STATEMENT_LENGTH = 400
ELLIPSIS = "…"
SLOW_QUERY_MS = 100.0


def _compact(statement: str) -> str:
    collapsed = " ".join(statement.split())
    if len(collapsed) <= MAX_STATEMENT_LENGTH:
        return collapsed
    return collapsed[:MAX_STATEMENT_LENGTH] + ELLIPSIS


def log_queries(engine: AsyncEngine, *, with_statement: bool = True) -> None:
    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def _before(  # pyright: ignore[reportUnusedFunction]
        connection: Connection,
        _cursor: Any,  # noqa: ANN401
        _statement: str,
        _parameters: Any,  # noqa: ANN401
        _context: ExecutionContext | None,
        _executemany: bool,  # noqa: FBT001
    ) -> None:
        connection.info[STARTED_KEY] = time.perf_counter()

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def _after(  # pyright: ignore[reportUnusedFunction]
        connection: Connection,
        cursor: Any,  # noqa: ANN401
        statement: str,
        _parameters: Any,  # noqa: ANN401
        _context: ExecutionContext | None,
        _executemany: bool,  # noqa: FBT001
    ) -> None:
        started = connection.info.pop(STARTED_KEY, None)
        if started is None:
            return

        duration = round((time.perf_counter() - started) * MILLISECONDS, 1)
        payload: dict[str, Any] = {
            "duration_ms": duration,
            "row_count": cursor.rowcount,
        }
        if with_statement:
            payload["statement"] = _compact(statement)

        if duration >= SLOW_QUERY_MS:
            logger.warning("db_query_slow", **payload)
        else:
            logger.debug("db_query", **payload)
