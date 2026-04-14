# ---------- constants ----------

DEFAULT_FAIL_THRESHOLD = 3
DEFAULT_RESET_TIMEOUT = 10

DEFAULT_RETRY_ATTEMPTS = 5
DEFAULT_BACKOFF = 0.5

HTTP_CONNECT_TIMEOUT = 2.0
HTTP_READ_TIMEOUT = 5.0
HTTP_WRITE_TIMEOUT = 5.0
HTTP_POOL_TIMEOUT = 2.0

HTTP_MAX_CONNECTIONS = 100
HTTP_MAX_KEEPALIVE_CONNECTIONS = 20


# ---------- imports ----------
import asyncio
import logging
from typing import Any
from collections.abc import Callable, Awaitable

import httpx
import random

from source.api_gateway.core.exceptions import (
    ExternalServiceException,
    TimeoutException,
    ServiceUnavailableException,
)

logger = logging.getLogger(__name__)


# ---------- retry ----------

async def retry(
    fn: Callable[[], Awaitable[Any]],
    attempts: int = DEFAULT_RETRY_ATTEMPTS,
    backoff: float = DEFAULT_BACKOFF,
) -> Any:
    for attempt in range(attempts):
        try:
            return await fn()

        except Exception as e:
            if attempt == attempts - 1:
                raise

            sleep_time = backoff * (2 ** attempt)
            sleep_time *= random.random()

            logger.warning(
                "Retrying request",
                extra={
                    "attempt": attempt + 1,
                    "sleep": sleep_time,
                    "error": str(e),
                },
            )

            await asyncio.sleep(sleep_time)


# ---------- circuit breaker ----------

class CircuitBreaker:
    def __init__(
        self,
        fail_threshold: int = DEFAULT_FAIL_THRESHOLD,
        reset_timeout: int = DEFAULT_RESET_TIMEOUT,
    ):
        self.fail_threshold = fail_threshold
        self.reset_timeout = reset_timeout

        self.fail_count = 0
        self.state = "CLOSED"  # CLOSED | OPEN | HALF_OPEN

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

class BaseClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

        self.client: httpx.AsyncClient | None = None
        self.cb = CircuitBreaker()

    # ---- lifecycle ----

    async def start(self):
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(
                connect=HTTP_CONNECT_TIMEOUT,
                read=HTTP_READ_TIMEOUT,
                write=HTTP_WRITE_TIMEOUT,
                pool=HTTP_POOL_TIMEOUT,
            ),
            limits=httpx.Limits(
                max_connections=HTTP_MAX_CONNECTIONS,
                max_keepalive_connections=HTTP_MAX_KEEPALIVE_CONNECTIONS,
            ),
        )

    async def close(self):
        if self.client:
            await self.client.aclose()

    # ---- request ----

    async def _request(self, method: str, url: str, **kwargs) -> Any:
        client = self.client
        if client is None:
            raise RuntimeError("HTTP client not initialized")

        async def do_request() -> Any:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

        async def wrapped() -> Any:
            return await self.cb.call(do_request)

        try:
            return await retry(wrapped)

        # ---- error mapping ----

        except httpx.TimeoutException:
            logger.error("Timeout calling external service", extra={"url": url})
            raise TimeoutException("external_service")

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error from external service",
                extra={
                    "url": url,
                    "status_code": e.response.status_code,
                    "body": e.response.text,
                },
            )
            raise ExternalServiceException("external_service", str(e))

        except httpx.RequestError as e:
            logger.error(
                "Service unavailable",
                extra={"url": url, "error": str(e)},
            )
            raise ServiceUnavailableException(str(e))