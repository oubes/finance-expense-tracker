from __future__ import annotations

from adapters.base_adapter import APIClient


class IngestionClient:
    def __init__(self, api_client: APIClient) -> None:
        self.api = api_client
        
    def health_check(self) -> dict:
        return self.api.get("/api/v1/ingestion/health")


    def start_ingestion(self, file_name: str, content: str) -> dict:
        return self.api.post(
            "/api/v1/ingestion",
            json={
                "file_name": file_name,
                "content": content,
            },
        )

    def get_status(self, job_id: str) -> dict:
        return self.api.get(f"/api/v1/ingestion/{job_id}")