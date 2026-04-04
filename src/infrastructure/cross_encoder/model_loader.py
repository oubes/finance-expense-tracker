from fastapi import Depends
import logging
from sentence_transformers import CrossEncoder
from src.core.config.loader import load_settings
import torch

logger = logging.getLogger(__name__)

settings = load_settings()

class ModelLoader:
    def __init__(self):
        logger.info("Initializing ModelLoader")
        self.model_name = settings.rag.cross_encoder_model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Using device: %s", self.device)
        self._model = None

    def load_model(self) -> CrossEncoder:
        logger.debug("load_model called")
        if self._model is None:
            logger.info("Loading CrossEncoder model: %s", self.model_name)
            self._model = CrossEncoder(
                self.model_name,
                device=self.device
            )
            logger.info("Model loaded successfully")
        else:
            logger.debug("Model already loaded")
        return self._model

    def get_model(self) -> CrossEncoder:
        logger.debug("get_model called")
        return self.load_model()

    def get_device(self) -> str:
        logger.debug("get_device called: %s", self.device)
        return self.device