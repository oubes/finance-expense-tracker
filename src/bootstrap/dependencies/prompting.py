# ---- Standard Library ----
import logging

# ---- FastAPI ----
from fastapi import Depends

# ---- Infrastructure ----
from src.bootstrap.dependencies.llm import get_llm_generator
from src.infrastructure.llm.llm_generator import LLMGenerator
from src.bootstrap.dependencies.settings import get_settings
from src.core.config.settings import AppSettings

# ---- Prompts ----
from src.modules.prompts.prompt_loader import PromptLoader
from src.modules.prompts.prompt_registry import PromptRegistry
from src.modules.prompts.processing.llm_json_validator import LLMJsonValidator
from src.modules.prompts.processing.llm_json_extractor import LLMJsonExtractor
from src.modules.prompts.msg_builder import MsgBuilder

# ---- Services ----
from src.services.llm_services.safe_generator import SafeGenerator

logger = logging.getLogger(__name__)


# ---- Prompt Loader ----
def get_prompt_loader() -> PromptLoader:
    logger.info("Initializing Prompt Loader")
    return PromptLoader()


# ---- Prompt Registry ----
def register_prompts(settings: AppSettings = Depends(get_settings)) -> PromptRegistry:
    logger.info("Registering prompts")
    return PromptRegistry(settings)


# ---- JSON Validator ----
def get_llm_json_validator() -> LLMJsonValidator:
    logger.info("Initializing LLM JSON Validator")
    return LLMJsonValidator()


# ---- JSON Extractor ----
def get_llm_json_extractor() -> LLMJsonExtractor:
    logger.info("Initializing LLM JSON Extractor")
    return LLMJsonExtractor()


# ---- Message Builder ----
def get_msg_builder(
    prompt_loader: PromptLoader = Depends(get_prompt_loader),
    registry: PromptRegistry = Depends(register_prompts),
) -> MsgBuilder:
    logger.info("Initializing Message Builder")
    return MsgBuilder(
        prompt_loader=prompt_loader,
        registry=registry,
    )
    
async def get_safe_generator(
    msg_builder: MsgBuilder = Depends(get_msg_builder),
    llm_generator: LLMGenerator = Depends(get_llm_generator),
    extractor: LLMJsonExtractor = Depends(get_llm_json_extractor),
    validator: LLMJsonValidator = Depends(get_llm_json_validator),
) -> SafeGenerator:
    logger.info("Initializing Safe Generator")
    return SafeGenerator(
        msg_builder=msg_builder,
        llm_generator=llm_generator,
        extractor=extractor,
        validator=validator,
    )