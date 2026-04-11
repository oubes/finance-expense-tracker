# ---- Standard Library ----
import logging

# ---- FastAPI ----
from fastapi import Depends

# ---- Core ----
from src.core.config.settings import AppSettings
from src.bootstrap.dependencies.settings_dep import get_settings

# ---- Infrastructure ----
from src.bootstrap.dependencies.embeddings_dep import get_embedding
from src.bootstrap.dependencies.prompting_dep import get_safe_generator
from src.bootstrap.dependencies.llm_dep import get_llm_generator
from src.infrastructure.vector_db.core.db_client import PostgresVectorClient
from src.bootstrap.dependencies.vector_db_dep import (
    get_db_client,
    get_init_chunks_table,
    get_upsert_chunks,
    get_delete_all_chunks,
    get_count_chunks,
)

# ---- Modules ----
from src.modules.ingestion.loader.pdf_loader import PyPDFDocumentLoader, PyMuPDFDocumentLoader
from src.modules.ingestion.chunker.cleaner_pre import PreTextCleaner
from src.modules.ingestion.chunker.cleaner_post import PostTextCleaner
from src.modules.ingestion.chunker.spiltter import Splitter
from src.modules.ingestion.chunker.toc_classifier import TOCClassifier
from src.modules.ingestion.chunker.validator import TextValidator
from src.modules.ingestion.chunker.scoring import ChunkScorer
from src.modules.ingestion.chunker.chunker import Chunker

from src.pipelines.v1.ingestion_pipeline import IngestionPipeline

# ---- Workflow ----
from src.workflow.ingestion_workflow import IngestionWorkflow

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- PDF Loader ----
def get_pdf_loader(settings: AppSettings = Depends(get_settings)) -> PyPDFDocumentLoader:
    return PyPDFDocumentLoader(settings)

def get_pymupdf_loader(settings: AppSettings = Depends(get_settings)) -> PyMuPDFDocumentLoader:
    return PyMuPDFDocumentLoader(settings)


# ---- Chunking Components ----
def get_chunker_pre_cleaner() -> PreTextCleaner:
    return PreTextCleaner()


def get_chunker_post_cleaner() -> PostTextCleaner:
    return PostTextCleaner()


def get_chunker_validator() -> TextValidator:
    return TextValidator()


def get_chunker_toc_classifier() -> TOCClassifier:
    return TOCClassifier()


def get_chunker_splitter(settings: AppSettings = Depends(get_settings)) -> Splitter:
    return Splitter(settings=settings)


def get_chunk_scorer(settings: AppSettings = Depends(get_settings)) -> ChunkScorer:
    return ChunkScorer(settings=settings)


def get_chunker(
    settings: AppSettings = Depends(get_settings),
    pre_cleaner: PreTextCleaner = Depends(get_chunker_pre_cleaner),
    post_cleaner: PostTextCleaner = Depends(get_chunker_post_cleaner),
    validator: TextValidator = Depends(get_chunker_validator),
    toc_classifier: TOCClassifier = Depends(get_chunker_toc_classifier),
    splitter: Splitter = Depends(get_chunker_splitter),
    scorer: ChunkScorer = Depends(get_chunk_scorer),
) -> Chunker:
    return Chunker(
        config=settings,
        pre_cleaner=pre_cleaner,
        post_cleaner=post_cleaner,
        validator=validator,
        toc_classifier=toc_classifier,
        splitter=splitter,
        scorer=scorer,
    )


# ---- Ingestion Pipeline ----
def get_ingestion_pipeline(
    settings: AppSettings = Depends(get_settings),
    pdf_loader: PyMuPDFDocumentLoader = Depends(get_pymupdf_loader),
    chunker: Chunker = Depends(get_chunker),
    embedding=Depends(get_embedding),
    safe_generator=Depends(get_safe_generator),
) -> IngestionPipeline:
    return IngestionPipeline(
        config=settings,
        pdf_loader=pdf_loader,
        chunker=chunker,
        embedding=embedding,
        safe_generator=safe_generator,
    )


# ---- Workflow Entrypoint ----
async def get_ingestion_workflow_entrypoint(
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
    db_client: PostgresVectorClient = Depends(get_db_client),
    init_table_fn = Depends(get_init_chunks_table),
    upsert_fn = Depends(get_upsert_chunks),
    delete_fn = Depends(get_delete_all_chunks),
    count_fn = Depends(get_count_chunks),
) -> IngestionWorkflow:

    return IngestionWorkflow(
        pipeline=pipeline,
        db_client=db_client,
        init_table_fn=init_table_fn,
        upsert_fn=upsert_fn,
        delete_fn=delete_fn,
        count_fn=count_fn,
    )