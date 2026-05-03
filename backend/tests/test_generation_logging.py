import logging
from pathlib import Path

from app.core.config import Settings
from app.core.logging import GENERATION_LOG_HANDLER_NAME, GENERATION_LOGGER_NAMES, configure_generation_logging


def test_configure_generation_logging_writes_pretty_progress_log(tmp_path: Path) -> None:
    log_file = tmp_path / "generation.log"
    settings = Settings(generation_log_file=str(log_file))
    logger = logging.getLogger(GENERATION_LOGGER_NAMES[0])
    original_handlers = {logger_name: list(logging.getLogger(logger_name).handlers) for logger_name in GENERATION_LOGGER_NAMES}

    try:
        for logger_name in GENERATION_LOGGER_NAMES:
            current_logger = logging.getLogger(logger_name)
            current_logger.handlers = [handler for handler in current_logger.handlers if handler.name != GENERATION_LOG_HANDLER_NAME]
        configure_generation_logging(settings)
        configure_generation_logging(settings)

        generation_handlers = [handler for handler in logger.handlers if handler.name == GENERATION_LOG_HANDLER_NAME]
        assert len(generation_handlers) == 1

        logger.info(
            "contents.assets.generating content_id=%s progress=%s/%s asset_id=%s",
            "content_test",
            1,
            10,
            "asset_test",
        )
        logger.info("contents.asset.succeeded content_id=%s asset_id=%s elapsed_sec=%.1f", "content_test", "asset_test", 1.2)
        generation_handlers[0].flush()

        log_text = log_file.read_text(encoding="utf-8")
        assert "] INFO contents.assets.generating content_id=content_test progress=1/10 asset_id=asset_test" in log_text
        assert "] INFO contents.asset.succeeded content_id=content_test asset_id=asset_test elapsed_sec=1.2" in log_text
    finally:
        for logger_name, handlers in original_handlers.items():
            logging.getLogger(logger_name).handlers = handlers
