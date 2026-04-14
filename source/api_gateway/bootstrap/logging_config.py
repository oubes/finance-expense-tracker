# ---- Imports ----
import logging
import sys
from logging.handlers import RotatingFileHandler


# ---- Logging Setup ----
def setup_logging(log_level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # ---- Console Handler ----
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # ---- File Handler (Rotating) ----
    file_handler = RotatingFileHandler(
        "app.log",
        maxBytes=100 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setLevel(log_level)

    # ---- Format ----
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # ---- Attach ----
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)