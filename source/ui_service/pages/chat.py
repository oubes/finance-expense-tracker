import streamlit as st

from application.chat_service import ChatService


def render(chat_service: ChatService) -> None:
    st.title("Chat")

    msg = st.text_input("Message")

    if st.button("Send"):
        chat_service.send_message(msg)

    for m in st.session_state.get("messages", []):
        st.write(f"{m['role']}: {m['content']}")