# ---- Imports ----
from source.chat_service.api.routes.chat_routes import router as chat_router
from source.chat_service.api.routes.test_routes import router as test_router

def register_routes(app):
    app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
    app.include_router(test_router, prefix="/api/test", tags=["Test"])
    return app