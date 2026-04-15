from __future__ import annotations

import streamlit as st

from adapters.ingestion_adapter import IngestionClient


class IngestionService:
    def __init__(self, ingestion_client: IngestionClient) -> None:
        self.client = ingestion_client
        
    def health_check(self) -> dict:
        return self.client.health_check()

    def upload(self, file_name: str, content: str) -> dict:
        response: dict = self.client.start_ingestion(file_name, content)

        st.session_state["last_job_id"] = response.get("job_id")

        return response

    def status(self, job_id: str) -> dict:
        return self.client.get_status(job_id)