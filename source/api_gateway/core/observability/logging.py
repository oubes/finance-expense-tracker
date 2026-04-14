# ---- Imports ----
import logging
import sys
from logging.handlers import RotatingFileHandler


# ---- ANSI Colors ----
class Colors:
    RESET = "\033[0m"
    GREY = "\033[90m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"


LEVEL_PREFIX = {
    "DEBUG": "🔵 ",
    "INFO": "🟢 ",
    "WARNING": "🟡 ",
    "ERROR": "🔴 ",
    "CRITICAL": "🟣 ",
}


# ---- Keys to exclude from extra (IMPORTANT FIX) ----
SKIP_KEYS = {
    "name", "msg", "args",
    "levelname", "levelno",
    "pathname", "filename",
    "module",
    "exc_info", "exc_text",
    "stack_info",
    "lineno", "funcName",
    "created", "msecs", "relativeCreated",
    "thread", "threadName",
    "processName", "process",
    "asctime",
    "message",
}


# ---- Custom Formatter ----
class ExtraFormatter(logging.Formatter):
    MAX_VALUE_LENGTH = 120
    SEPARATOR = f"{Colors.GREY}{'-' * 120}{Colors.RESET}"

    def _flatten_value(self, v):
        if isinstance(v, dict):
            return "{" + ", ".join(
                f"{k}={self._flatten_value(val)}"
                for k, val in v.items()
            ) + "}"

        if isinstance(v, (list, tuple)):
            return "[" + ", ".join(map(str, v[:5])) + ("..." if len(v) > 5 else "") + "]"

        s = str(v).replace("\n", " ").replace("\r", " ")

        if len(s) > self.MAX_VALUE_LENGTH:
            s = s[:self.MAX_VALUE_LENGTH] + "..."

        return s

    def format(self, record):
        base = super().format(record)

        extras = {
            k: self._flatten_value(v)
            for k, v in record.__dict__.items()
            if k not in SKIP_KEYS
        }

        prefix = LEVEL_PREFIX.get(record.levelname, "⚪")

        line = f"{prefix} {record.levelname} | {base}"

        if extras:
            line += f" | extra={extras}"

        return f"{line}\n{self.SEPARATOR}"


# ---- Fix: unify uvicorn + fastapi logging ----
def _attach_uvicorn_to_root():
    for name in [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
    ]:
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = False


# ---- Logging Setup ----
def setup_logging(log_level=logging.INFO):
    logger = logging.getLogger()

    # prevent duplicate handlers
    logger.handlers.clear()
    logger.setLevel(log_level)

    # ---- Console Handler ----
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # ---- File Handler ----
    file_handler = RotatingFileHandler(
        "app.log",
        maxBytes=100 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setLevel(log_level)

    # ---- Formatters ----
    console_formatter = ExtraFormatter(
        "%(asctime)s | %(name)s | %(message)s"
    )

    file_formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )

    console_handler.setFormatter(console_formatter)
    file_handler.setFormatter(file_formatter)

    # ---- Attach ----
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # ---- IMPORTANT FIX ----
    _attach_uvicorn_to_root()