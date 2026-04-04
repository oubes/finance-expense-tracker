import logging
from src.infrastructure.cross_encoder.model_loader import ModelLoader

logger = logging.getLogger(__name__)


class Encoder:
    def __init__(self, model_loader: ModelLoader | None = None):
        logger.info("Initializing Encoder")
        self.model_loader = model_loader or ModelLoader()
        self.model = self.model_loader.get_model()
        logger.info("Encoder initialized successfully")

    def score_pair(self, query: str, document: str) -> float:
        logger.debug("Scoring single pair")
        score = self.model.predict([(query, document)])
        result = float(score[0])
        logger.debug("Score computed: %f", result)
        return result

    def score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        logger.debug("Scoring %d pairs", len(pairs))
        scores = self.model.predict(pairs)
        result = [float(s) for s in scores]
        logger.debug("Batch scoring completed")
        return result

    def score_documents(self, query: str, documents: list[str]) -> list[float]:
        logger.debug("Scoring %d documents for query", len(documents))
        pairs = [(query, doc) for doc in documents]
        return self.score_pairs(pairs)