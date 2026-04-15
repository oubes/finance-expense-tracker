import time
import logging

from source.api_gateway.core.observability.context import get_trace_id

logger = logging.getLogger(__name__)


class Span:
    def __init__(self, name: str):
        self.name = name
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000

        logger.info(
            "[SPAN] name=%s trace_id=%s duration_ms=%.2f",
            self.name,
            get_trace_id(),
            duration_ms,
        )