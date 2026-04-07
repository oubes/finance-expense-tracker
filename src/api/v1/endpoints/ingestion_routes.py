# ---- Imports ----
import logging

# ---- FastAPI ----
from fastapi import APIRouter, Depends

# ---- Pipeline ----
from src.bootstrap.dependencies.ingestion import get_ingestion_workflow_entrypoint

# ---- Logger ----
logger = logging.getLogger(__name__)

# ---- Router ----
router = APIRouter()


# ---- Run Ingestion Workflow ----
@router.post("/run")
def run_ingestion_workflow(
    workflow = Depends(get_ingestion_workflow_entrypoint),
):
    logger.info("Starting ingestion workflow execution")

    result = workflow.run()

    logger.info("Ingestion workflow execution completed")

    return {
        "status": "success",
        "result": result,
    }
