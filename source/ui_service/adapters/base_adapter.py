from __future__ import annotations

import httpx


class APIClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.client = httpx.Client()

    def post(self, path: str, json: dict, timeout: float = 10.0) -> dict:
        url = f"{self.base_url}{path}"
        response = self.client.post(url, json=json, timeout=timeout)
        response.raise_for_status()
        return response.json()

    def get(self, path: str, params: dict | None = None, timeout: float = 10.0) -> dict:
        url = f"{self.base_url}{path}"
        response = self.client.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()