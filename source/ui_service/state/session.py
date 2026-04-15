import streamlit as st

def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "session_id" not in st.session_state:
        st.session_state.session_id = "default"

def add_message(role: str, content: str) -> None:
    st.session_state.messages.append({
        "role": role,
        "content": content
    })

def get_messages() -> list:
    return st.session_state.messages