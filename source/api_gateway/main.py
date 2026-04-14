# ---- Imports ----
from source.api_gateway.core.app.app_factory import create_app
from source.api_gateway.core.logging import setup_logging

# ---- Setup Logging ----
setup_logging()

# ---- App Instance ----
app = create_app()
