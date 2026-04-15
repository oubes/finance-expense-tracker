# ---- Imports ----
import time
from source.api_gateway.core.observability.context import get_trace_id


class Span:
    def __init__(self, name: str):
        self.name = name
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000

        trace_id = get_trace_id()

        print(
            f"[TRACE] trace_id={trace_id} "
            f"span={self.name} "
            f"duration_ms={duration_ms:.2f}"
        )