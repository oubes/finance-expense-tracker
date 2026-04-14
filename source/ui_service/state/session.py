import streamlit as st

def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []

def add_message(role: str, content: str):
    st.session_state.messages.append({
        "role": role,
        "content": content
    })

def get_messages():
    return st.session_state.messages