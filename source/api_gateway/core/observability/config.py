# ---- Imports ----
from pydantic import BaseModel


class ObservabilityConfig(BaseModel):
    service_name: str = "unknown-service"
    log_level: str = "INFO"

    enable_tracing: bool = True
    enable_metrics: bool = True

    enable_console_logging: bool = True
    enable_file_logging: bool = True

    log_file_path: str = "app.log"
    max_log_size_mb: int = 100
    log_backup_count: int = 5


config = ObservabilityConfig()