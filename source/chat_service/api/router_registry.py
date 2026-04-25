# ---- Imports ----
from source.chat_service.api.routes.chat_routes import router as ingestion_router

def register_routes(app):
    app.include_router(ingestion_router, prefix="/api/ingestion", tags=["ingestion"])
    return app