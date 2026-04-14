import logging
from typing import Any

from source.api_gateway.clients.base import BaseClient

logger = logging.getLogger(__name__)


# ------------- Chat Service Client -------------
class ChatClient(BaseClient):

    # ------------- Initialize -------------
    def __init__(self, base_url: str):
        logger.info("[CHAT_CLIENT] initializing | base_url=%s", base_url)
        super().__init__(base_url)
        logger.info("[CHAT_CLIENT] initialized successfully")

    # ------------- Chat Endpoint -------------
    async def chat(self, payload: dict) -> Any:
        logger.info("[CHAT_CLIENT] chat request started")

        try:
            result = await self._request(
                "POST",
                "/chat",
                json=payload,
            )

            logger.info("[CHAT_CLIENT] chat SUCCESS")
            return result

        except Exception:
            logger.exception("[CHAT_CLIENT] chat FAILED")
            raise

    # ------------- Health Check -------------
    async def health(self) -> dict:
        logger.info("[CHAT_CLIENT] health check started")

        try:
            await self._request(
                "GET",
                "/health",
            )

            logger.info("[CHAT_CLIENT] health OK")
            return {
                "service": "chat",
                "status": "up",
            }

        except Exception:
            logger.exception("[CHAT_CLIENT] health FAILED")

            return {
                "service": "chat",
                "status": "down",
            }