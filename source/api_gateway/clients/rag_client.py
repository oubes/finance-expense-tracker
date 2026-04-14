import logging
from source.api_gateway.clients.base_client import BaseClient

# ---- Logger ----
logger = logging.getLogger(__name__)


# ------------- RAG Service Client -------------
class RAGClient(BaseClient):

    # ------------- Initialize with Chat Timeout -------------
    def __init__(self, base_url: str):
        logger.info("[RAG_CLIENT] initializing | base_url=%s", base_url)
        super().__init__(base_url, timeout=10.0)
        logger.info("[RAG_CLIENT] initialized successfully")

    # ------------- Chat Endpoint -------------
    async def chat(self, payload: dict):

        logger.info("[RAG_CLIENT] chat request started")

        try:
            result = await self._request(
                "POST",
                f"{self.base_url}/chat",
                json=payload
            )

            logger.info("[RAG_CLIENT] chat SUCCESS")
            return result

        except Exception as e:
            logger.exception(
                "[RAG_CLIENT] chat FAILED | error=%s",
                str(e)
            )
            raise