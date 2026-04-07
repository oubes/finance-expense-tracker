# ---- Standard Library ----
import logging

# ---- Infrastructure ----
from src.infrastructure.cross_encoder.model_loader import ModelLoader as CrossEncoderModelLoader
from src.infrastructure.cross_encoder.encoder import Encoder as CrossEncoder

logger = logging.getLogger(__name__)


# ---- Cross Encoder Model ----
def get_cross_encoder_model() -> CrossEncoderModelLoader:
    logger.info("Loading cross encoder model")
    return CrossEncoderModelLoader()


# ---- Cross Encoder ----
def get_cross_encoder(model: CrossEncoderModelLoader = get_cross_encoder_model()) -> CrossEncoder:
    logger.info("Initializing Cross Encoder")
    return CrossEncoder(model_loader=model)