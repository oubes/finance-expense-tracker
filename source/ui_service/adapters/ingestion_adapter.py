# ----------- Imports -----------
from __future__ import annotations

import logging
import httpx

from adapters.base_adapter import APIClient
from core.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)

# ----------- Client -----------
class IngestionClient:
    def __init__(self, api_client: APIClient) -> None:
        self.api = api_client

    def health_check(self) -> dict:
        try:
            return self.api.get(
                "/api/v1/ingestion/health",
                timeout=3.0,
            )
        except httpx.TimeoutException as e:
            logger.error("Ingestion health_check timeout")
            raise ServiceUnavailableError("Ingestion service is not responding")

    def start_ingestion(self, file_name: str, content: str) -> dict:
        try:
            return self.api.post(
                "/api/v1/ingestion",
                json={
                    "file_name": file_name,
                    "content": content,
                },
                timeout=10.0,
            )
        except httpx.TimeoutException as e:
            logger.error("Ingestion start timeout")
            raise ServiceUnavailableError("Ingestion service is not responding")

    def get_status(self, job_id: str) -> dict:
        try:
            return self.api.get(
                f"/api/v1/ingestion/{job_id}",
                timeout=5.0,
            )
        except httpx.TimeoutException as e:
            logger.error("Ingestion get_status timeout")
            raise ServiceUnavailableError("Ingestion service is not responding")