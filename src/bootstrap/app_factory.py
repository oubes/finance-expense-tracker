from fastapi import FastAPI
from src.bootstrap.lifespan import lifespan
from src.bootstrap.middleware import register_middleware
from src.bootstrap.router import register_routes


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    register_middleware(app)
    register_routes(app)
    
    return app