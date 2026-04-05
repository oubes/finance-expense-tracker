# ---- Imports ----
from fastapi import FastAPI
from src.bootstrap.lifespan import lifespan
from src.bootstrap.middleware import register_middleware
from src.bootstrap.router import register_routes


# ---- Application Factory ----
def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    # ---- Middleware Registration ----
    register_middleware(app)

    # ---- Routes Registration ----
    register_routes(app)
    
    return app