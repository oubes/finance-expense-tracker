from __future__ import annotations

from adapters.base_adapter import APIClient

class ChatClient:
    def __init__(self, api_client: APIClient) -> None:
        self.api = api_client

    def send_message(self, message: str, session_id: str) -> dict:
        return self.api.post(
            "/api/v1/chat",
            json={
                "message": message,
                "session_id": session_id,
            },
        )

    def get_chat(self, chat_id: str) -> dict:
        return self.api.get(f"/api/v1/chat/{chat_id}")