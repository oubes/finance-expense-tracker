from fastapi import Depends
from functools import lru_cache

# ---- Settings ----
from source.ingestion_service.core.config.settings import AppSettings

# ---- Clients ----
from source.ingestion_service.adapters import LLMClient, EmbeddingClient, VectorDBClient

# ---- Services ----
from source.ingestion_service.application import LLMService, EmbeddingService, VectorDBService

# ---- PDF Loader ----
from source.ingestion_service.processing.loader.pdf_loader import PyMuPDFDocumentLoader

# ---- Chunking Components ----
from source.ingestion_service.processing.chunker import (
    PreTextCleaner,
    PostTextCleaner,
    TextValidator,
    TOCClassifier,
    Splitter,
    ChunkScorer,
    Chunker,
)

# ---- Workflow ----
from source.ingestion_service.workflow.ingestion_workflow import IngestionWorkflow


def get_settings() -> AppSettings:
    return AppSettings()

# ---- Client ----
def get_llm_client(settings: AppSettings = Depends(get_settings)) -> LLMClient:
    return LLMClient(settings=settings)

def get_embedding_client(settings: AppSettings = Depends(get_settings)) -> EmbeddingClient:
    return EmbeddingClient(settings=settings)

def get_vector_db_client(settings: AppSettings = Depends(get_settings)) -> VectorDBClient:
    return VectorDBClient(settings=settings)


#--- Services ----
def get_llm_service(llm_client: LLMClient = Depends(get_llm_client)) -> LLMService:
    return LLMService(llm_client)

def get_embedding_service(embedding_client: EmbeddingClient = Depends(get_embedding_client)) -> EmbeddingService:
    return EmbeddingService(embedding_client)

def get_vector_db_service(vector_db_client: VectorDBClient = Depends(get_vector_db_client)) -> VectorDBService:
    return VectorDBService(vector_db_client)


# ---- PDF Loader ----
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

# ---- Workflow Entrypoint ----
# async def get_ingestion_workflow_entrypoint(

# ) -> IngestionWorkflow:
#     pdf_loader: PyPDFDocumentLoader = Depends(get_pdf_loader)
#     chunker: Chunker = Depends(get_chunker)
#     return IngestionWorkflow(

#     )