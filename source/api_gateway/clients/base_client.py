import httpx
import asyncio
import logging

# ---- Logger ----
logger = logging.getLogger(__name__)


# ------------- Circuit Breaker Implementation -------------
class CircuitBreaker:

    def __init__(self, fail_threshold: int = 3, reset_timeout: int = 10):
        self.fail_threshold = fail_threshold
        self.reset_timeout = reset_timeout
        self.fail_count = 0
        self.is_open = False

        logger.info(
            "[CIRCUIT_BREAKER] initialized | threshold=%s reset_timeout=%ss",
            fail_threshold,
            reset_timeout
        )

    # ------------- Execute Protected Call -------------
    async def call(self, func, *args, **kwargs):

        if self.is_open:
            logger.warning("[CIRCUIT_BREAKER] call blocked (OPEN state)")
            raise Exception("Circuit breaker is OPEN")

        try:
            logger.debug("[CIRCUIT_BREAKER] executing protected call")

            result = await func(*args, **kwargs)

            self.fail_count = 0

            logger.info("[CIRCUIT_BREAKER] call success | fail_count reset")
            return result

        except Exception as e:
            self.fail_count += 1

            logger.warning(
                "[CIRCUIT_BREAKER] call failed | fail_count=%s | error=%s",
                self.fail_count,
                str(e)
            )

            if self.fail_count >= self.fail_threshold:
                self.is_open = True
                logger.error("[CIRCUIT_BREAKER] OPENED due to threshold breach")
                asyncio.create_task(self._reset())

            raise

    # ------------- Reset Circuit After Cooldown -------------
    async def _reset(self):

        logger.info("[CIRCUIT_BREAKER] reset timer started | sleep=%ss", self.reset_timeout)

        await asyncio.sleep(self.reset_timeout)

        self.fail_count = 0
        self.is_open = False

        logger.info("[CIRCUIT_BREAKER] RESET COMPLETE | state=CLOSED")


# ------------- Base HTTP Client with Pooling + Retry + CB -------------
class BaseClient:

    def __init__(self, base_url: str, timeout: float):

        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=timeout)
        self.cb = CircuitBreaker()

        logger.info(
            "[BASE_CLIENT] initialized | base_url=%s timeout=%ss",
            base_url,
            timeout
        )

    # ------------- Core Request Handler (Retry + CB) -------------
    async def _request(self, method: str, url: str, **kwargs):

        logger.info("[BASE_CLIENT] request started | %s %s", method, url)

        async def do_request():
            logger.debug("[BASE_CLIENT] executing HTTP call via httpx")
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

        # ------------- Retry Loop -------------
        for attempt in range(3):
            try:
                result = await self.cb.call(do_request)

                logger.info(
                    "[BASE_CLIENT] request success | attempt=%s %s %s",
                    attempt + 1,
                    method,
                    url
                )

                return result

            except Exception as e:

                logger.warning(
                    "[BASE_CLIENT] request failed | attempt=%s %s %s | error=%s",
                    attempt + 1,
                    method,
                    url,
                    str(e)
                )

                if attempt == 2:
                    logger.error("[BASE_CLIENT] request exhausted retries | %s %s", method, url)
                    raise

                await asyncio.sleep(0.5 * (attempt + 1))