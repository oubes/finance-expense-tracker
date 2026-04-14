import streamlit as st


def render_chat_box(messages):
    for msg in messages:
        render_message(msg)


def render_message(msg):
    role = msg.get("role", "ai")
    msg_type = msg.get("type", "text")
    content = msg.get("content", "")

    with st.chat_message(role):

        if msg_type == "error":
            st.error(content)

        elif msg_type == "system":
            st.info(content)

        elif msg_type == "tool":
            st.code(content)

        else:
            st.write(content)