from src.api.v1.endpoints.health_routes import router as health_router

def register_routes(app):
    app.include_router(health_router, prefix="/api/v1/health", tags=["health"])