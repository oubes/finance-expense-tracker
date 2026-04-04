import time
import asyncio
import redis.asyncio as redis
import logging
from src.core.config.settings import AppSettings
from src.api.v1.schemas.health_schemas import DependencyResult, RedisHealthData

# Initialize logger
logger = logging.getLogger(__name__)

async def check_redis(settings: AppSettings, timeout: float = 1.0) -> DependencyResult:
    """
    Check Redis availability using PING command.
    """
    start = time.perf_counter()
    r_conf = settings.redis
    
    logger.info("Starting Redis health check")
    try:
        client = redis.from_url(r_conf.full_url, socket_timeout=timeout)
        async with asyncio.timeout(timeout):
            pong = await client.ping()
        
        latency = (time.perf_counter() - start) * 1000
        status_val = "success" if pong else "failed"
        
        data = RedisHealthData(
            healthy=bool(pong), 
            detail="ok" if pong else "No pong response", 
            latency_ms=latency
        )
        
        logger.info(f"Redis health check: {status_val}")
        return DependencyResult(status=status_val, data=data.model_dump())

    except Exception as e:
        logger.exception("Redis health check failed")
        return DependencyResult(
            status="failed",
            error=str(e),
        )