import streamlit as st

from application.ingestion_service import IngestionService


def render(ingestion_service: IngestionService) -> None:
    if st.button("Health Check"):
        response = ingestion_service.health_check()
        st.write(response)