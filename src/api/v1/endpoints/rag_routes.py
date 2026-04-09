# ---- Imports ----
import logging
from fastapi import APIRouter, Depends
from src.bootstrap.dependencies.rag import get_rag_workflow

# ---- Logger ----
logger = logging.getLogger(__name__)

# ---- Router ----
router = APIRouter()


# ---- Run RAG Workflow ----
@router.post("/run")
async def run_rag_workflow(
    workflow = Depends(get_rag_workflow),
):
    logger.info("Starting rag workflow execution")

    result = await workflow.run()

    logger.info("Rag workflow execution completed")

    return {
        "status": "success",
        "result": result,
    }