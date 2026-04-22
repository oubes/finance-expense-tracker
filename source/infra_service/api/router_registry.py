# ---- Imports ----
from source.infra_service.api.routes.health_routes import router as health_router
from source.infra_service.api.routes.llm_routes import router as llm_router
from source.infra_service.api.routes.embedder_routes import router as embedder_router

from source.infra_service.api.routes.chunks_db_routes import router as chunks_db_router
from source.infra_service.api.routes.semantic_memory_routes import router as semantic_memory_router
from source.infra_service.api.routes.transactions_memory_routes import router as transactions_memory_router
from source.infra_service.api.routes.user_facts_memory_routes import router as user_facts_memory_router


#--- Router Registry ----
def register_routes(app):
    # ---- Health ----
    app.include_router(health_router, prefix="/api/infra/health", tags=["Health"])
    
    # ---- LLM ----
    app.include_router(llm_router, prefix="/api/infra/llm", tags=["LLM"])
    
    # ---- Embedder ----
    app.include_router(embedder_router, prefix="/api/infra/embedding", tags=["Embedder"])
    
    # ---- Memory ----
    app.include_router(chunks_db_router, prefix="/api/infra/chunks_db", tags=["Chunks Database"])
    app.include_router(semantic_memory_router, prefix="/api/infra/semantic_memory", tags=["Semantic Memory"])
    app.include_router(transactions_memory_router, prefix="/api/infra/transactions_memory", tags=["Transactions Memory"])
    app.include_router(user_facts_memory_router, prefix="/api/infra/user_facts_memory", tags=["User Facts Memory"])
    
    return app