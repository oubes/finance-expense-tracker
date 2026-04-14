# ---------- chat service ----------

from source.api_gateway.clients.chat import ChatClient


class ChatService:
    def __init__(self, chat_client: ChatClient):
        self.chat_client = chat_client

    async def handle_message(self, message: str):
        return await self.chat_client.chat({"message": message})