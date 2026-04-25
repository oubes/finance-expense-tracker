from fastapi import Depends, Request
from functools import lru_cache

# ---- Settings ----
from source.chat_service.core.config.settings import AppSettings

# ---- Clients ----
from source.chat_service.adapters import LLMClient, EmbeddingClient, VectorDBClient

# ---- Services ----
from source.chat_service.application import LLMService, EmbeddingService, VectorDBService


@lru_cache()
def get_settings() -> AppSettings:
    return AppSettings()

# ---- Client ----
@lru_cache()
def get_llm_client(request: Request) -> LLMClient:
    return request.app.state.llm_client

@lru_cache()
def get_embedding_client(request: Request) -> EmbeddingClient:
    return request.app.state.embedding_client

@lru_cache()
def get_vector_db_client(request: Request) -> VectorDBClient:
    return request.app.state.vector_db_client


#--- Services ----
def get_llm_service(llm_client: LLMClient = Depends(get_llm_client)) -> LLMService:
    return LLMService(llm_client)

def get_embedding_service(embedding_client: EmbeddingClient = Depends(get_embedding_client)) -> EmbeddingService:
    return EmbeddingService(embedding_client)

def get_vector_db_service(vector_db_client: VectorDBClient = Depends(get_vector_db_client)) -> VectorDBService:
    return VectorDBService(vector_db_client)


