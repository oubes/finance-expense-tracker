from __future__ import annotations

import streamlit as st

from adapters.chat_adapter import ChatClient


class ChatService:
    def __init__(self, chat_client: ChatClient) -> None:
        self.client = chat_client

    def send_message(self, message: str) -> dict:
        session_id: str = st.session_state.get("session_id", "default")

        response: dict = self.client.send_message(
            message=message,
            session_id=session_id,
        )

        st.session_state.setdefault("messages", [])

        st.session_state["messages"].append(
            {"role": "user", "content": message}
        )
        st.session_state["messages"].append(
            {"role": "assistant", "content": response.get("answer")}
        )

        return response