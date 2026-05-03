import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import Settings

GENERATION_LOGGER_NAMES = (
    "app.api.routes.ai",
    "app.api.routes.contents",
    "app.ai.openai_provider",
    "app.ai.elevenlabs_provider",
)
GENERATION_LOG_HANDLER_NAME = "eduyj_generation_file"


class GenerationLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.level_short = record.levelname[:4]
        return super().format(record)


def configure_generation_logging(settings: Settings) -> None:
    log_path = Path(settings.generation_log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = _get_or_create_generation_handler(log_path)
    handler.setLevel(logging.INFO)

    for logger_name in GENERATION_LOGGER_NAMES:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = True
        if not any(existing.name == GENERATION_LOG_HANDLER_NAME for existing in logger.handlers):
            logger.addHandler(handler)


def _get_or_create_generation_handler(log_path: Path) -> RotatingFileHandler:
    resolved_log_path = log_path.resolve()
    for logger_name in GENERATION_LOGGER_NAMES:
        for handler in logging.getLogger(logger_name).handlers:
            if handler.name == GENERATION_LOG_HANDLER_NAME and isinstance(handler, RotatingFileHandler):
                if Path(handler.baseFilename).resolve() == resolved_log_path:
                    return handler
                _remove_generation_handler(handler)
                break

    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    handler.name = GENERATION_LOG_HANDLER_NAME
    handler.setFormatter(GenerationLogFormatter("[%(asctime)s] %(level_short)s %(message)s", datefmt="%H:%M:%S"))
    return handler


def _remove_generation_handler(handler: RotatingFileHandler) -> None:
    for logger_name in GENERATION_LOGGER_NAMES:
        logger = logging.getLogger(logger_name)
        logger.handlers = [existing for existing in logger.handlers if existing is not handler]
    handler.close()
