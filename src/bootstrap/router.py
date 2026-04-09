# ---- Imports ----
from src.api.v1.endpoints.health_routes import router as health_router
from src.api.v1.endpoints.ingestion_routes import router as ingestion_router
from src.api.v1.endpoints.rag_routes import router as rag_router


# ---- Routes Registration ----
def register_routes(app):
    app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
    app.include_router(ingestion_router, prefix="/api/v1/ingestion", tags=["ingestion"])
    app.include_router(rag_router, prefix="/api/v1/rag", tags=["rag"])
    
    return app