# ---------- imports ----------
import asyncio
import logging
from typing import Any
from collections.abc import Callable, Awaitable

import httpx
import random

from source.api_gateway.core.config.settings import Settings
from source.api_gateway.core.errors.exceptions import (
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
    for attempt in range(attempts):
        try:
            logger.info(
                "retry_attempt_start",
                extra={
                    "attempt": attempt + 1,
                    "max_attempts": attempts,
                },
            )

            return await fn()

        except Exception as e:
            if attempt == attempts - 1:
                logger.error(
                    "retry_exhausted",
                    extra={
                        "attempt": attempt + 1,
                        "max_attempts": attempts,
                        "error": str(e),
                    },
                )
                raise

            sleep_time = backoff * (2 ** attempt)
            jittered_sleep = sleep_time * random.random()

            logger.warning(
                "retry_backoff",
                extra={
                    "attempt": attempt + 1,
                    "sleep_s": round(jittered_sleep, 3),
                },
            )

            await asyncio.sleep(jittered_sleep)


# ---------- circuit breaker ----------
class CircuitBreaker:
    def __init__(self, settings: Settings):
        self.fail_threshold = settings.CB_FAIL_THRESHOLD
        self.reset_timeout = settings.CB_RESET_TIMEOUT

        self.fail_count = 0
        self.state = "CLOSED"

        self._lock = asyncio.Lock()

    async def call(self, fn: Callable[[], Awaitable[Any]]) -> Any:
        async with self._lock:
            if self.state == "OPEN":
                logger.error(
                    "circuit_breaker_open_block",
                    extra={
                        "fail_count": self.fail_count,
                        "threshold": self.fail_threshold,
                    },
                )
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

                logger.warning(
                    "circuit_breaker_failure",
                    extra={
                        "fail_count": self.fail_count,
                        "threshold": self.fail_threshold,
                        "state": self.state,
                    },
                )

                if self.fail_count >= self.fail_threshold:
                    self.state = "OPEN"
                    asyncio.create_task(self._reset())

            raise

    async def _reset(self):
        await asyncio.sleep(self.reset_timeout)

        async with self._lock:
            self.state = "HALF_OPEN"
            self.fail_count = 0

            logger.warning(
                "circuit_breaker_half_open",
                extra={"state": self.state},
            )


# ---------- base client ----------
class BaseClient:
    def __init__(self, base_url: str, settings: Settings):
        self.base_url = base_url
        self.settings = settings

        self.client: httpx.AsyncClient | None = None
        self.cb = CircuitBreaker(self.settings)

    async def start(self):
        logger.info(
            "http_client_init",
            extra={"base_url": self.base_url},
        )

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

        logger.info("http_client_ready")

    async def close(self):
        if self.client:
            await self.client.aclose()
            logger.info("http_client_closed")

    async def _request(self, method: str, url: str, **kwargs) -> Any:
        client = self.client

        if client is None:
            logger.critical("http_client_not_initialized")
            raise RuntimeError("HTTP client not initialized")

        logger.info(
            "http_request_start",
            extra={
                "method": method,
                "url": url,
            },
        )

        async def do_request() -> Any:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

        async def wrapped() -> Any:
            return await self.cb.call(do_request)

        try:
            result = await retry(
                wrapped,
                attempts=self.settings.RETRY_ATTEMPTS,
                backoff=self.settings.RETRY_BACKOFF,
            )

            logger.info(
                "http_request_success",
                extra={
                    "method": method,
                    "url": url,
                },
            )

            return result

        except httpx.TimeoutException:
            logger.error("http_timeout", extra={"url": url})
            raise TimeoutException("external_service")

        except httpx.HTTPStatusError as e:
            logger.error(
                "http_status_error",
                extra={
                    "url": url,
                    "status_code": e.response.status_code,
                },
            )
            raise ExternalServiceException("external_service", str(e))

        except httpx.RequestError:
            logger.error("http_network_error", extra={"url": url})
            raise ServiceUnavailableException("external_service")