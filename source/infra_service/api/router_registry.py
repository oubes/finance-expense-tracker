# ---- Imports ----
from source.infra_service.api.routes.health_routes import router as health_router
from source.infra_service.api.routes.llm_routes import router as llm_router
from source.infra_service.api.routes.embedder_routes import router as embedder_router
from source.infra_service.api.routes.chunks_db_routes import router as chunks_db_router


def register_routes(app):
    app.include_router(health_router, prefix="/api/infra/health", tags=["health"])
    app.include_router(llm_router, prefix="/api/infra/llm", tags=["llm"])
    app.include_router(embedder_router, prefix="/api/infra/embedding", tags=["embedder"])
    app.include_router(chunks_db_router, prefix="/api/infra/chunks", tags=["chunks"])
    return app