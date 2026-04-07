# ---- Standard Library ----
import logging

# ---- FastAPI ----
from fastapi import Depends

# ---- Core Config ----
from src.core.config.settings import AppSettings
from src.bootstrap.dependencies.settings import get_settings

# ---- Infrastructure ----
from src.infrastructure.embeddings.model_loader import ModelLoader as EmbedModelLoader
from src.infrastructure.embeddings.embedder import Embedder

logger = logging.getLogger(__name__)


# ---- Embedding Model ----
def get_embedding_model(settings: AppSettings = Depends(get_settings)) -> EmbedModelLoader:
    logger.info("Loading embedding model")
    return EmbedModelLoader(settings)


# ---- Embedder ----
def get_embedding(model: EmbedModelLoader = Depends(get_embedding_model)) -> Embedder:
    logger.info("Initializing Embedding")
    return Embedder(model_loader=model)