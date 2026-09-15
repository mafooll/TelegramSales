import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from structlog.types import Processor

CALLSITE_PARAMETERS = {
    structlog.processors.CallsiteParameter.MODULE,
    structlog.processors.CallsiteParameter.FUNC_NAME,
    structlog.processors.CallsiteParameter.LINENO,
}
LOG_FILE_NAME = "bot.log"
BYTES_IN_MEGABYTE = 1024 * 1024


def _shared_processors() -> list["Processor"]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.CallsiteParameterAdder(CALLSITE_PARAMETERS),
    ]


def _console_handler(*, use_json: bool) -> logging.Handler:
    renderer: Processor = (
        structlog.processors.JSONRenderer()
        if use_json
        else structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.RichTracebackFormatter(
                max_frames=10,
                show_locals=False,
            ),
        )
    )
    handler = logging.StreamHandler()
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.TimeStamper(
                    fmt="iso" if use_json else "%H:%M:%S"
                ),
                renderer,
            ],
            foreign_pre_chain=_shared_processors(),
        )
    )
    return handler


def _file_handler(
    directory: Path,
    *,
    max_megabytes: int,
    backups: int,
) -> logging.Handler:
    directory.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        directory / LOG_FILE_NAME,
        maxBytes=max_megabytes * BYTES_IN_MEGABYTE,
        backupCount=backups,
        encoding="utf-8",
    )
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            foreign_pre_chain=_shared_processors(),
        )
    )
    return handler


def setup_logging(
    log_level: str = "INFO",
    *,
    use_json: bool = False,
    log_directory: Path | None = None,
    max_megabytes: int = 10,
    backups: int = 5,
) -> None:
    structlog.configure(
        processors=[
            *_shared_processors(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    handlers = [_console_handler(use_json=use_json)]
    if log_directory is not None:
        handlers.append(
            _file_handler(
                log_directory,
                max_megabytes=max_megabytes,
                backups=backups,
            )
        )

    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    for handler in handlers:
        root.addHandler(handler)
    root.setLevel(log_level)
