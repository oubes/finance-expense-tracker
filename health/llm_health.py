import time
import asyncio
import logging
from src.infrastructure.llm.model_loader import LLMClient
from src.api.v1.schemas.health_schemas import DependencyResult, LLMHealthData

# Initialize logger
logger = logging.getLogger(__name__)

class LLMHealth:
    """
    Check LLM provider health by sending a minimal test prompt.
    """
    def __init__(self):
        self.client = LLMClient()
        self.model_name = self.client.model

    async def check(self, timeout: float = 3.0) -> DependencyResult:
        start = time.perf_counter()
        logger.info(f"Starting LLM health check for model: {self.model_name}")
        
        try:
            async with asyncio.timeout(timeout):
                # Call LLM in a thread to avoid blocking if the client is synchronous
                response = await asyncio.to_thread(
                    self.client.client.chat.completions.create,
                    model=self.model_name,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=1,
                    temperature=0.0,
                )
            
            if not response or not response.choices:
                raise ValueError("Empty response from LLM provider")

            latency = (time.perf_counter() - start) * 1000
            data = LLMHealthData(
                healthy=True, 
                model=self.model_name, 
                latency_ms=latency, 
                detail="ok" # type: ignore
            )
            
            logger.info("LLM health check successful")
            return DependencyResult(status="success", data=data.model_dump())

        except Exception as e:
            logger.exception("LLM health check failed")
            return DependencyResult(
                status="failed",
                error=str(e),
            )