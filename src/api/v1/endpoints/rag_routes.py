# ---- Imports ----
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.bootstrap.dependencies.rag_dep import get_rag_workflow

# ---- Logger ----
logger = logging.getLogger(__name__)

# ---- Router ----
router = APIRouter()


# ---- Request Schema ----
class RAGRequest(BaseModel):
    user_query: str


# ---- Run RAG Workflow ----
@router.post("/run_workflow")
async def run_rag_workflow(
    body: RAGRequest,
    workflow=Depends(get_rag_workflow),
):
    logger.info("Starting rag workflow execution")

    result = await workflow.run(user_query=body.user_query)

    logger.info("Rag workflow execution completed")

    return {
        "status": "success",
        "result": result,
    }