import logging
import logging.handlers
import os
import sys
from pathlib import Path


def setup_logger(name: str = "family_budget", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    try:
        from app.config import settings
        log_dir = settings.log_dir_path
        log_file = os.path.join(log_dir, "app.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass  # Log dir may not be available in tests

    return logger


def get_logger(name: str) -> logging.Logger:
    from app.config import settings
    return setup_logger(name, settings.LOG_LEVEL)


# Root app logger
logger = get_logger("family_budget")
