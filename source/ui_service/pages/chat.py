import streamlit as st
from components.chat_box import render_chat_box
from state.session import init_state, add_message, get_messages

def render_chat():
    st.title("Chat UI")

    init_state()

    messages = get_messages()

    render_chat_box(messages)

    user_input = st.chat_input("Type message...")

    if user_input:
        add_message("user", user_input)
        add_message("assistant", f"Echo: {user_input}")
        st.rerun()