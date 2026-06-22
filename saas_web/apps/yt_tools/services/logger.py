"""
Centralised logging for the VidSnap clip pipeline.
Writes structured logs both to console (stdout) and to a log file.
"""
import logging
import sys
from pathlib import Path


def setup_logger(name: str = 'vidsnap') -> logging.Logger:
    """Create a logger that writes to stdout and a rotating log file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if this module is reloaded
    if logger.handlers:
        return logger

    # ── console handler (stdout) ──────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)-8s %(name)s | %(message)s',
        datefmt='%H:%M:%S',
    ))
    logger.addHandler(console)

    # ── file handler ──────────────────────────────────────────────
    try:
        log_dir = Path(__file__).resolve().parent.parent.parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / 'vidsnap.log'

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)-8s %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        ))
        logger.addHandler(file_handler)
    except Exception:
        pass  # non-blocking — logs will still go to console

    return logger


# Default module-level logger
log = setup_logger()
