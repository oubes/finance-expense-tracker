# ---- Imports ----
from source.chat_service.api.routes.chat_routes import router as chat_router

def register_routes(app):
    app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
    return app