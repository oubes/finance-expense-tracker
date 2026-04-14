# ---- Imports ----
from source.api_gateway.bootstrap.app_factory import create_app
from source.api_gateway.core.dependencies import get_settings
from source.api_gateway.bootstrap.logging_config import setup_logging

# ---- Setup Logging ----
setup_logging()

# ---- App Instance ----
app = create_app()
