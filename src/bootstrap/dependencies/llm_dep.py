# ---- Standard Library ----
import logging

# ---- FastAPI ----
from fastapi import Depends

# ---- Core Config ----
from src.core.config.settings import AppSettings
from src.bootstrap.dependencies.settings_dep import get_settings

# ---- Infrastructure ----
from src.infrastructure.llm.model_loader import LLMClient
from src.infrastructure.llm.llm_generator import LLMGenerator

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- LLM Client ----
def get_llm_client(settings: AppSettings = Depends(get_settings)) -> LLMClient:
    logger.info("Initializing LLM Client")
    return LLMClient(settings=settings)


# ---- LLM Generator ----
def get_llm_generator(
    llm_client: LLMClient = Depends(get_llm_client),
    settings: AppSettings = Depends(get_settings),
)-> LLMGenerator:
    logger.info("Initializing LLM Generator")
    return LLMGenerator(llm=llm_client, settings=settings)

