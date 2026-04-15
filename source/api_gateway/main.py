# ---- Imports ----
from source.api_gateway.core.bootstrap.app_factory import create_app
from source.api_gateway.core.observability import setup_logging

# ---- Setup Logging ----
setup_logging()

# ---- App Instance ----
app = create_app()
