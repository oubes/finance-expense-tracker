# ---- Imports ----
import logging
import sys
from logging.handlers import RotatingFileHandler

from source.api_gateway.core.observability.context import (
    get_request_id,
    get_trace_id,
    get_service_name,
)


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


# ---- Keys to exclude from extra ----
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


# ---- Context Filter (Observability Injection) ----
class ContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        record.trace_id = get_trace_id()
        record.service_name = get_service_name()
        return True


# ---- Custom Formatter (extra + readability) ----
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


# ---- Uvicorn / FastAPI logging isolation ----
def _attach_uvicorn_to_root():
    for name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = False


# ---- Logging Setup ----
def setup_logging(log_level=logging.INFO):
    logger = logging.getLogger()

    logger.handlers.clear()
    logger.setLevel(log_level)

    # ---- Console ----
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    console_formatter = ExtraFormatter(
        "%(asctime)s | %(name)s | svc=%(service_name)s | req=%(request_id)s | trace=%(trace_id)s | %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(ContextFilter())

    # ---- File ----
    file_handler = RotatingFileHandler(
        "app.log",
        maxBytes=100 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setLevel(log_level)

    file_formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(ContextFilter())

    # ---- Attach ----
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    _attach_uvicorn_to_root()