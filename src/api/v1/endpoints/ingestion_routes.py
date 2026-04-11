# ---- Imports ----
import logging
from fastapi import APIRouter, Depends
from src.bootstrap.dependencies.ingestion_dep import get_ingestion_workflow_entrypoint

# ---- Logger ----
logger = logging.getLogger(__name__)

# ---- Router ----
router = APIRouter()


# ---- Run Ingestion Workflow ----
@router.post("/run")
async def run_ingestion_workflow(
    workflow = Depends(get_ingestion_workflow_entrypoint),
):
    logger.info("Starting ingestion workflow execution")

    result = await workflow.run()

    logger.info("Ingestion workflow execution completed")

    return {
        "status": "success",
        "result": result,
    }