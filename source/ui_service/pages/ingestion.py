# ----------- Imports -----------
import streamlit as st

from application.ingestion_service import IngestionService
from core.exceptions import ServiceUnavailableError

# ----------- Ingestion Page -----------
def render(ingestion_service: IngestionService) -> None:
    if st.button("Health Check"):
        try:
            with st.spinner("Checking health..."):
                response = ingestion_service.health_check()
                st.write(response)

        except ServiceUnavailableError:
            st.error("Service is currently unavailable. Please try again later.")

        except Exception:
            st.error("Unexpected error occurred.")