# ---- Imports ----
from collections import defaultdict
import time


class Metrics:
    def __init__(self):
        self.counters = defaultdict(int)
        self.latencies = defaultdict(list)

    def inc(self, name: str, value: int = 1):
        self.counters[name] += value

    def observe_latency(self, name: str, duration_ms: float):
        self.latencies[name].append(duration_ms)

    def time_block(self, name: str):
        return _Timer(self, name)

    def snapshot(self):
        return {
            "counters": dict(self.counters),
            "latency_avg": {
                k: (sum(v) / len(v) if v else 0)
                for k, v in self.latencies.items()
            },
        }


class _Timer:
    def __init__(self, metrics: Metrics, name: str):
        self.metrics = metrics
        self.name = name
        self.start: float = 0.0

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start) * 1000
        self.metrics.observe_latency(self.name, duration_ms)


metrics = Metrics()