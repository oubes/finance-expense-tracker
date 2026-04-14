import streamlit as st

from pages.home import render_home
from pages.chat import render_chat

st.set_page_config(page_title="UI Service", layout="centered")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Chat"])

if page == "Home":
    render_home()
elif page == "Chat":
    render_chat()