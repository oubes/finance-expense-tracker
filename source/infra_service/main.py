# ---- Imports ----
from source.infra_service.core.observability.logging import setup_logging
from source.infra_service.core.bootstrap.app_factory import create_app

# ---- Setup Logging ----
setup_logging()

# ---- Create FastAPI App ----
app = create_app()