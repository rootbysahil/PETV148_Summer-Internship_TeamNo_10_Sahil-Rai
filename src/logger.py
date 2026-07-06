import hashlib
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from config import settings


def setup_logger(name: str = "smft") -> logging.Logger:
    """Configures and returns a rotating logger setup.

    Args:
        name: Name of the logger instance.

    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL.upper())

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(filename)s:%(lineno)d] - %(message)s"
    )

    # Under Vercel Serverless environment, we only log to StreamHandler (stdout)
    if os.environ.get("VERCEL"):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        logger.propagate = False
        return logger

    # Rotating File Handler
    log_file_path = settings.LOG_DIR / "smft.log"
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Prevent propagation to root logger to control stdout output entirely through UI module
    logger.propagate = False

    return logger


def mask_username(username: str) -> str:
    """Masks or hashes a username for logging if privacy mode is enabled.

    Args:
        username: The username to mask.

    Returns:
        str: Masked username or hash.
    """
    if settings.MASK_USERNAME_IN_LOGS:
        hashed = hashlib.sha256(username.encode("utf-8")).hexdigest()
        return f"[MASKED_{hashed[:12]}]"
    return username
