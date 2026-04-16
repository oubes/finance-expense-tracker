# ---- Imports ----
from source.api_gateway.api.routes.ingestion_routes import router as ingestion_router

# ---- Routes Registration ----
def register_routes(app):
    app.include_router(ingestion_router, prefix="/api", tags=["ingestion"])
    return app