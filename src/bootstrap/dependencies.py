# ---- Standard Library ----
import logging

# ---- FastAPI ----
from fastapi import Depends

# ---- Core Config ----
from src.core.config.loader import load_settings
from src.core.config.settings import AppSettings

# ---- Infrastructure ----
from src.infrastructure.embeddings.model_loader import ModelLoader as EmbedModelLoader
from src.infrastructure.embeddings.embedder import Embedder
from src.infrastructure.cross_encoder.model_loader import ModelLoader as CrossEncoderModelLoader
from src.infrastructure.cross_encoder.encoder import Encoder as CrossEncoder
from src.infrastructure.llm.model_loader import LLMClient
from src.infrastructure.llm.llm_generator import LLMGenerator

# ---- Vector DB ----
from src.infrastructure.vector_db.core.db_conn import DBConnect
from src.infrastructure.vector_db.core.db_exec import DBExecutor
from src.infrastructure.vector_db.extensions.db_vector_ext import VectorExtension
from src.infrastructure.vector_db.core.db_client import PostgresVectorClient
from src.infrastructure.vector_db.queries.chunk_queries import (
    CREATE_CHUNKS_TABLE_SQL, INSERT_CHUNK_SQL, DELETE_CHUNKS_SQL,
    COUNT_CHUNKS_SQL, PREVIEW_CHUNKS_SQL, SEARCH_CHUNKS_SQL
)
from src.infrastructure.vector_db.operations.chunk_ops import (
    init_chunks_table, upsert_chunks, delete_all_chunks,
    count_chunks, preview_chunks, search_chunks
)

# ---- Retrieval / RAG ----
from src.modules.rag.retrieval.bm25_retrieval import BM25Retriever
from src.modules.rag.retrieval.vector_retriever import VectorRetriever
from src.modules.rag.retrieval.hybrid_retriever import HybridRetriever
from src.modules.rag.retrieval.queries import VECTOR_SEARCH_QUERY, BM25_SEARCH_QUERY

# ---- LLM Prompting / Generation ----
from src.modules.prompts.prompt_loader import PromptLoader
from src.modules.prompts.prompt_registry import PromptRegistry
from src.modules.prompts.processing.llm_json_validator import LLMJsonValidator
from src.modules.prompts.processing.llm_json_extractor import LLMJsonExtractor
from src.modules.prompts.msg_builder import MsgBuilder

# ---- Ingestion ----
from src.modules.ingestion.chunker.cleaner_pre import PreTextCleaner
from src.modules.ingestion.chunker.cleaner_post import PostTextCleaner
from src.modules.ingestion.chunker.spiltter import Splitter
from src.modules.ingestion.chunker.toc_classifier import TOCClassifier
from src.modules.ingestion.chunker.validator import TextValidator
from src.modules.ingestion.loader.pdf_loader import PDFDocumentLoader
from src.modules.ingestion.chunker.scoring import ChunkScorer
from src.modules.ingestion.chunker.chunker import Chunker

# ---- Ingestion Pipeline ----
from src.pipelines.v1.ingestion_pipeline import IngestionPipeline

# ---- Ingestion Service ----
from src.services.v1.chunk_ingestion_service import ChunkIngestionService

# ---- Logger ----
logger = logging.getLogger(__name__)

# ---- Core Config ----

def get_settings() -> AppSettings:
    logger.info("Loading application settings")
    return load_settings()

# ---- LLM ----

def get_llm_client(settings: AppSettings = Depends(get_settings)) -> LLMClient:
    logger.info("Initializing LLM Client")
    return LLMClient(settings=settings)


def get_llm_generator(llm_client: LLMClient = Depends(get_llm_client)) -> LLMGenerator:
    logger.info("Initializing LLM Generator")
    return LLMGenerator(llm=llm_client)

# ---- Models ----

def get_embedding_model(settings: AppSettings = Depends(get_settings)) -> EmbedModelLoader:
    logger.info("Loading embedding model")
    return EmbedModelLoader(settings)


def get_embedding(model: EmbedModelLoader = Depends(get_embedding_model)) -> Embedder:
    logger.info("Initializing Embedding")
    return Embedder(model_loader=model)


def get_cross_encoder_model() -> CrossEncoderModelLoader:
    logger.info("Loading cross encoder model")
    return CrossEncoderModelLoader()


def get_cross_encoder(model: CrossEncoderModelLoader = Depends(get_cross_encoder_model)) -> CrossEncoder:
    logger.info("Initializing Cross Encoder")
    return CrossEncoder(model_loader=model)

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


def get_pdf_loader() -> PDFDocumentLoader:
    logger.info("Initializing PDF Document Loader")
    return PDFDocumentLoader()

# ---- DB Lifecycle ----

async def get_db_connection(settings: AppSettings = Depends(get_settings)) -> DBConnect:
    logger.info("Creating DB connection")
    conn = DBConnect(settings=settings)

    if hasattr(conn, "connect") and callable(conn.connect):
        result = conn.connect()
        if hasattr(result, "__await__"):
            await result
        else:
            await conn.connect()

    return conn


async def get_db_executor(conn: DBConnect = Depends(get_db_connection)) -> DBExecutor:
    logger.info("Creating DB executor")
    return DBExecutor(conn)


async def get_vector_extension(conn: DBConnect = Depends(get_db_connection)) -> VectorExtension:
    logger.info("Creating Vector Extension")
    vector_ext = VectorExtension(conn.conn)
    await vector_ext.enable()
    return vector_ext

# ---- DB Client ----

async def get_db_client(
    conn: DBConnect = Depends(get_db_connection),
    executor: DBExecutor = Depends(get_db_executor),
    vector_ext: VectorExtension = Depends(get_vector_extension),
) -> PostgresVectorClient:
    logger.info("Creating PostgresVectorClient")

    client = PostgresVectorClient(
        conn=conn,
        db_executor=executor,
        vector_ext=vector_ext,
    )

    ok = await client.init()
    if not ok:
        raise RuntimeError("Failed to initialize PostgresVectorClient")

    return client

# ---- Retrievers ----

def get_bm25_retriever(db_client: PostgresVectorClient = Depends(get_db_client)) -> BM25Retriever:
    logger.info("Initializing BM25 Retriever")
    return BM25Retriever(db_client=db_client, query_sql=BM25_SEARCH_QUERY)


def get_vector_retriever(
    db_client: PostgresVectorClient = Depends(get_db_client),
    embedding_model: EmbedModelLoader = Depends(get_embedding_model),
) -> VectorRetriever:
    logger.info("Initializing Vector Retriever")
    return VectorRetriever(
        db_client=db_client,
        embedding_fn=embedding_model,
        query_sql=VECTOR_SEARCH_QUERY,
    )


def get_hybrid_retriever(
    bm25: BM25Retriever = Depends(get_bm25_retriever),
    vector: VectorRetriever = Depends(get_vector_retriever),
) -> HybridRetriever:
    logger.info("Initializing Hybrid Retriever")
    return HybridRetriever(bm25=bm25, vector=vector)

# ---- Prompt / Generation ----

def get_prompt_loader() -> PromptLoader:
    logger.info("Initializing Prompt Loader")
    return PromptLoader()


def register_prompts(settings: AppSettings = Depends(get_settings)) -> PromptRegistry:
    logger.info("Registering prompts")
    return PromptRegistry(settings)


def get_llm_json_validator() -> LLMJsonValidator:
    logger.info("Initializing LLM JSON Validator")
    return LLMJsonValidator()


def get_llm_json_extractor() -> LLMJsonExtractor:
    logger.info("Initializing LLM JSON Extractor")
    return LLMJsonExtractor()


def get_msg_builder(
    prompt_loader: PromptLoader = Depends(get_prompt_loader),
    registry: PromptRegistry = Depends(register_prompts),
) -> MsgBuilder:
    logger.info("Initializing Message Builder")
    return MsgBuilder(
        prompt_loader=prompt_loader,
        registry=registry,
    )

# ---- Ingestion Pipeline ----

def get_ingestion_pipeline(
    settings: AppSettings = Depends(get_settings),
    pdf_loader: PDFDocumentLoader = Depends(get_pdf_loader),
    chunker: Chunker = Depends(get_chunker),
    embedding: Embedder = Depends(get_embedding),
    msg_builder: MsgBuilder = Depends(get_msg_builder),
    llm_generator: LLMGenerator = Depends(get_llm_generator),
    json_extractor: LLMJsonExtractor = Depends(get_llm_json_extractor),
    json_validator: LLMJsonValidator = Depends(get_llm_json_validator),
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

async def get_ingestion_service(
    db_client: PostgresVectorClient = Depends(get_db_client),
) -> ChunkIngestionService:
    logger.info("Initializing Ingestion Service")
    return ChunkIngestionService(
        client=db_client,
        collection="chunk_embeddings",
    )
