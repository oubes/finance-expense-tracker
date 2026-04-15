import streamlit as st

from config.settings import Settings

from adapters.base_adapter import APIClient
from adapters.chat_adapter import ChatClient
from adapters.ingestion_adapter import IngestionClient

from application.chat_service import ChatService
from application.ingestion_service import IngestionService

from state.session import init_state

from pages.chat import render as chat_page
from pages.ingestion import render as ingestion_page


def build_services():
    api_client = APIClient("http://localhost:8000")

    return (
        ChatService(ChatClient(api_client)),
        IngestionService(IngestionClient(api_client)),
    )


def main():
    init_state()

    chat_service, ingestion_service = build_services()

    tab1, tab2 = st.tabs(["Chat", "Ingestion"])

    with tab1:
        chat_page(chat_service)

    with tab2:
        ingestion_page(ingestion_service)


if __name__ == "__main__":
    main()