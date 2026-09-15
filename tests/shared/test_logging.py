import json
import logging
from pathlib import Path

import structlog

from telegramsales.shared.logger_config import LOG_FILE_NAME, setup_logging


def read_lines(directory: Path) -> list[dict[str, object]]:
    text = (directory / LOG_FILE_NAME).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line]


def test_a_record_lands_in_the_file(tmp_path: Path) -> None:
    setup_logging(log_directory=tmp_path)

    structlog.get_logger().info("probe_event", order="2026-09-15-0001")
    logging.shutdown()

    written = read_lines(tmp_path)

    assert written[-1]["event"] == "probe_event"
    assert written[-1]["order"] == "2026-09-15-0001"


def test_a_record_keeps_its_callsite(tmp_path: Path) -> None:
    setup_logging(log_directory=tmp_path)

    structlog.get_logger().warning("callsite_event")
    logging.shutdown()

    written = read_lines(tmp_path)[-1]

    assert written["func_name"] == "test_a_record_keeps_its_callsite"
    assert written["module"] == "test_logging"
    assert written["level"] == "warning"


def test_the_bound_context_reaches_the_file(tmp_path: Path) -> None:
    setup_logging(log_directory=tmp_path)
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(update_id=42)

    structlog.get_logger().info("context_event")
    structlog.contextvars.clear_contextvars()
    logging.shutdown()

    assert read_lines(tmp_path)[-1]["update_id"] == 42


def test_a_foreign_logger_is_written_too(tmp_path: Path) -> None:
    setup_logging(log_directory=tmp_path)

    logging.getLogger("aiogram.dispatcher").info("Update id=1 is handled")
    logging.shutdown()

    written = read_lines(tmp_path)[-1]

    assert written["event"] == "Update id=1 is handled"
    assert written["logger"] == "aiogram.dispatcher"


def test_without_a_directory_nothing_is_written(tmp_path: Path) -> None:
    setup_logging(log_directory=None)

    structlog.get_logger().info("lost_event")

    assert not (tmp_path / LOG_FILE_NAME).exists()
