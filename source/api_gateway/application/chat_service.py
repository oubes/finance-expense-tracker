import logging
import time

from source.api_gateway.adapters.chat_adapter import ChatClient
from source.api_gateway.schemas.response.chat import ChatResponse

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, chat_client: ChatClient):
        self.chat_client = chat_client

    async def handle_message(self, message: str) -> ChatResponse:
        logger.info(
            "[CHAT_SERVICE] handle_message started",
            extra={"message_len": len(message)},
        )

        start = time.perf_counter()

        try:
            response = await self.chat_client.chat(
                {"message": message}
            )

            latency_ms = (time.perf_counter() - start) * 1000

            data = response.json() if hasattr(response, "json") else response

            return ChatResponse(
                status="up",
                data=data,
                error=None,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000

            logger.exception("[CHAT_SERVICE] handle_message failed")

            return ChatResponse(
                status="unreachable",
                data=None,
                error=str(e),
                latency_ms=latency_ms,
            )