from __future__ import annotations

import httpx


class APIClient:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def post(self, path: str, json: dict) -> dict:
        url = f"{self.base_url}{path}"
        response = self.client.post(url, json=json)
        response.raise_for_status()
        return response.json()

    def get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()