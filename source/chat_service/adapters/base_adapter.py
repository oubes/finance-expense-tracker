# ---------- imports ----------
import asyncio
from typing import Any
from collections.abc import Callable, Awaitable

import httpx
import random
import logging

from source.chat_service.core.config.settings import AppSettings
from source.chat_service.core.errors.exceptions import (
    ExternalServiceException,
    TimeoutException,
    ServiceUnavailableException,
)

logger = logging.getLogger(__name__)


# ---------- retry ----------
async def retry(
    fn: Callable[[], Awaitable[Any]],
    attempts: int,
    backoff: float,
) -> Any:
    last_error: Exception = RuntimeError("retry failed unexpectedly")

    for attempt in range(attempts):
        try:
            return await fn()

        except Exception as e:
            last_error = e

            if attempt == attempts - 1:
                raise

            sleep_time = backoff * (2 ** attempt)
            await asyncio.sleep(sleep_time * random.random())

    raise last_error


# ---------- circuit breaker ----------
class CircuitBreaker:
    def __init__(self, settings: AppSettings):
        self.fail_threshold = settings.CB_FAIL_THRESHOLD
        self.reset_timeout = settings.CB_RESET_TIMEOUT

        self.fail_count = 0
        self.state = "CLOSED"
        self._lock = asyncio.Lock()

    async def call(self, fn: Callable[[], Awaitable[Any]]) -> Any:
        async with self._lock:
            if self.state == "OPEN":
                raise ServiceUnavailableException("external_service")

        try:
            result = await fn()

            async with self._lock:
                self.fail_count = 0
                self.state = "CLOSED"

            return result

        except Exception:
            async with self._lock:
                self.fail_count += 1

                if self.fail_count >= self.fail_threshold:
                    self.state = "OPEN"
                    asyncio.create_task(self._reset())

            raise

    async def _reset(self):
        await asyncio.sleep(self.reset_timeout)

        async with self._lock:
            self.state = "HALF_OPEN"
            self.fail_count = 0


# ---------- base client ----------
class BaseAPIClient:
    def __init__(self, base_url: str, settings: AppSettings):
        self.base_url = base_url
        self.settings = settings
        self.client: httpx.AsyncClient | None = None
        self.cb = CircuitBreaker(settings)

    # lifecycle
    async def start(self):
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(
                connect=self.settings.HTTP_CONNECT_TIMEOUT,
                read=self.settings.HTTP_READ_TIMEOUT,
                write=self.settings.HTTP_WRITE_TIMEOUT,
                pool=self.settings.HTTP_POOL_TIMEOUT,
            ),
            limits=httpx.Limits(
                max_connections=self.settings.HTTP_MAX_CONNECTIONS,
                max_keepalive_connections=self.settings.HTTP_MAX_KEEPALIVE_CONNECTIONS,
            ),
        )

    async def close(self):
        if self.client is not None:
            await self.client.aclose()

    # core request
    async def _request(self, method: str, url: str, **kwargs) -> Any:
        client = self.client

        if client is None:
            raise RuntimeError("HTTP client not initialized")

        async def do_request() -> Any:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

        async def wrapped():
            return await self.cb.call(do_request)

        try:
            return await retry(
                wrapped,
                attempts=self.settings.RETRY_ATTEMPTS,
                backoff=self.settings.RETRY_BACKOFF,
            )

        except httpx.TimeoutException:
            logger.warning("timeout external call %s", url)
            raise TimeoutException("external_service")

        except httpx.HTTPStatusError as e:
            logger.error("http error %s", str(e))
            raise ExternalServiceException("external_service", str(e))

        except httpx.RequestError:
            logger.error("request error %s", url)
            raise ServiceUnavailableException("external_service")

    # helpers
    async def get(self, path: str, **kwargs) -> Any:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Any:
        return await self._request("POST", path, **kwargs)