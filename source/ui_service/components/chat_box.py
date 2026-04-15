import streamlit as st


def chat_box():
    st.subheader("Chat Box")

    for msg in st.session_state.get("messages", []):
        st.write(f"{msg['role']}: {msg['content']}")