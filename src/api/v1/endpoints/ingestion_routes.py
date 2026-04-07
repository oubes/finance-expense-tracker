# ---- Imports ----
import logging

# ---- FastAPI ----
from fastapi import APIRouter, Depends

# ---- Pipeline ----
from src.pipelines.v1.ingestion_pipeline import IngestionPipeline
from src.bootstrap.dependencies.ingestion import get_ingestion_pipeline

# ---- Logger ----
logger = logging.getLogger(__name__)

# ---- Router ----
router = APIRouter()


# ---- Run Ingestion Pipeline ----
@router.post("/run")
def run_ingestion_pipeline(
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
):
    logger.info("Starting ingestion pipeline execution")

    result = pipeline.run()

    logger.info("Ingestion pipeline execution completed")

    return {
        "status": "success",
        "result": result,
    }
