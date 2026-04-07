# ---- Standard Library ----
import logging

# ---- FastAPI ----
from fastapi import Depends

# ---- Core ----
from src.core.config.settings import AppSettings
from src.bootstrap.dependencies.settings import get_settings

# ---- Infrastructure ----
from src.bootstrap.dependencies.embeddings import get_embedding
from src.bootstrap.dependencies.llm import get_llm_generator
from src.infrastructure.vector_db.core.db_client import PostgresVectorClient
from src.bootstrap.dependencies.vector_db import get_db_client

# ---- Modules ----
from src.modules.ingestion.loader.pdf_loader import PDFDocumentLoader
from src.modules.ingestion.chunker.cleaner_pre import PreTextCleaner
from src.modules.ingestion.chunker.cleaner_post import PostTextCleaner
from src.modules.ingestion.chunker.spiltter import Splitter
from src.modules.ingestion.chunker.toc_classifier import TOCClassifier
from src.modules.ingestion.chunker.validator import TextValidator
from src.modules.ingestion.chunker.scoring import ChunkScorer
from src.modules.ingestion.chunker.chunker import Chunker

from src.pipelines.v1.ingestion_pipeline import IngestionPipeline
from src.services.v1.chunk_ingestion_service import ChunkIngestionService

# ---- Workflow ----
from src.workflow.ingestion_workflow import IngestionWorkflow

# ---- Prompting ----
from src.bootstrap.dependencies.prompting import (
    get_msg_builder,
    get_llm_json_extractor,
    get_llm_json_validator,
)

logger = logging.getLogger(__name__)


# ---- PDF Loader ----
def get_pdf_loader() -> PDFDocumentLoader:
    logger.info("Initializing PDF Document Loader")
    return PDFDocumentLoader()


# ---- Chunking Components ----
def get_chunker_pre_cleaner() -> PreTextCleaner:
    logger.info("Initializing Pre-Text Cleaner")
    return PreTextCleaner()


def get_chunker_post_cleaner() -> PostTextCleaner:
    logger.info("Initializing Post-Text Cleaner")
    return PostTextCleaner()


def get_chunker_validator() -> TextValidator:
    logger.info("Initializing Text Validator")
    return TextValidator()


def get_chunker_toc_classifier() -> TOCClassifier:
    logger.info("Initializing TOC Classifier")
    return TOCClassifier()


def get_chunker_splitter(settings: AppSettings = Depends(get_settings)) -> Splitter:
    logger.info("Initializing Text Splitter")
    return Splitter(settings=settings)


def get_chunk_scorer(settings: AppSettings = Depends(get_settings)) -> ChunkScorer:
    logger.info("Initializing Chunk Scorer")
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
    logger.info("Initializing Chunker")
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
    pdf_loader: PDFDocumentLoader = Depends(get_pdf_loader),
    chunker: Chunker = Depends(get_chunker),
    embedding=Depends(get_embedding),
    msg_builder=Depends(get_msg_builder),
    llm_generator=Depends(get_llm_generator),
    json_extractor=Depends(get_llm_json_extractor),
    json_validator=Depends(get_llm_json_validator),
) -> IngestionPipeline:
    logger.info("Initializing Ingestion Pipeline")
    return IngestionPipeline(
        config=settings,
        pdf_loader=pdf_loader,
        chunker=chunker,
        embedding=embedding,
        llm_generator=llm_generator,
        msg_builder=msg_builder,
        json_extractor=json_extractor,
        json_validator=json_validator,
    )


# ---- Ingestion Service ----
async def get_db_ingestion_service(
    db_client: PostgresVectorClient = Depends(get_db_client),
) -> ChunkIngestionService:
    logger.info("Initializing Ingestion Service")
    return ChunkIngestionService(
        client=db_client,
        collection="chunk_embeddings",
    )


# ---- Workflow Entrypoint ----
async def get_ingestion_workflow_entrypoint(
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
) -> IngestionWorkflow:
    logger.info("Starting Ingestion Workflow")

    workflow = IngestionWorkflow(pipeline=pipeline)
    return workflow