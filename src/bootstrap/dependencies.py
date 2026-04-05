# ---- Standard Library ----
import logging
from functools import lru_cache
from collections.abc import AsyncIterator

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
from src.infrastructure.vector_db.core.db_client import PostgresVectorClient
from src.infrastructure.vector_db.extensions.db_vector_ext import VectorExtension

# ---- Retrieval / RAG ----
from src.modules.retrieval.bm25_retrieval import BM25Retriever
from src.modules.retrieval.vector_retriever import VectorRetriever
from src.modules.retrieval.hybrid_retriever import HybridRetriever
from src.modules.retrieval.queries import VECTOR_SEARCH_QUERY, BM25_SEARCH_QUERY

# ---- Ingestion Pipeline ----
from src.modules.ingestion.chunker.cleaner import TextCleaner
from src.modules.ingestion.chunker.spiltter import Splitter
from src.modules.ingestion.chunker.toc_classifier import TOCClassifier
from src.modules.ingestion.chunker.validator import TextValidator
from src.modules.ingestion.loader.pdf_loader import PDFDocumentLoader
from src.modules.ingestion.chunker.scoring import ChunkScorer
from src.modules.ingestion.chunker.chunker import Chunker

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- Core Config ----
@lru_cache()
def get_settings() -> AppSettings:
    # Load and cache application-wide configuration
    logger.info("Loading application settings")
    return load_settings()


# ---- LLM ----
@lru_cache()
def get_llm_client() -> LLMClient:
    # Initialize LLM client using global settings
    logger.info("Initializing LLM Client")
    settings = get_settings()
    return LLMClient(settings=settings)


@lru_cache()
def get_llm_generator() -> LLMGenerator:
    # Wrap LLM client with generation interface
    logger.info("Initializing LLM Generator")
    llm_client = get_llm_client()
    return LLMGenerator(llm=llm_client)


# ---- Models (Singletons) ----
@lru_cache()
def get_embedding_model() -> EmbedModelLoader:
    # Load embedding model once and reuse across requests
    logger.info("Loading embedding model")
    settings = get_settings()
    loader = EmbedModelLoader(settings)
    return loader


@lru_cache()
def get_embedding() -> Embedder:
    # Initialize embedding wrapper around the model loader
    logger.info("Initializing Embedding")
    model = get_embedding_model()
    return Embedder(model_loader=model)


@lru_cache()
def get_cross_encoder_model() -> CrossEncoderModelLoader:
    # Load cross-encoder model for reranking tasks
    logger.info("Loading cross encoder model")
    loader = CrossEncoderModelLoader()
    return loader


@lru_cache()
def get_cross_encoder() -> CrossEncoder:
    # Initialize cross-encoder using the loaded model
    logger.info("Initializing Cross Encoder")
    model = get_cross_encoder_model()
    return CrossEncoder(model_loader=model)


# ---- Ingestion Dependencies ----
@lru_cache()
def get_chunker_cleaner() -> TextCleaner:
    # Initialize text cleaning component
    logger.info("Initializing Text Cleaner")
    text_cleaner = TextCleaner()
    return text_cleaner


@lru_cache()
def get_chunker_validator() -> TextValidator:
    # Initialize validation component for text chunks
    logger.info("Initializing Text Validator")
    text_validator = TextValidator()
    return text_validator


@lru_cache()
def get_chunker_toc_classifier() -> TOCClassifier:
    # Initialize table-of-contents classifier
    logger.info("Initializing TOC Classifier")
    toc_classifier = TOCClassifier()
    return toc_classifier


@lru_cache()
def get_chunker_splitter() -> Splitter:
    # Initialize text splitter using application settings
    logger.info("Initializing Text Splitter")
    settings = get_settings()
    return Splitter(settings=settings)


@lru_cache()
def get_chunk_scorer() -> ChunkScorer:
    # Initialize scoring component for chunk ranking
    logger.info("Initializing Chunk Scorer")
    settings = get_settings()
    return ChunkScorer(settings=settings)


@lru_cache()
def get_chunker() -> Chunker:
    # Compose full chunking pipeline from modular components
    logger.info("Initializing Chunker")
    settings = get_settings()
    cleaner = get_chunker_cleaner()
    validator = get_chunker_validator()
    toc_classifier = get_chunker_toc_classifier()
    splitter = get_chunker_splitter()
    scorer = get_chunk_scorer()
    return Chunker(
        config=settings,
        cleaner=cleaner,
        validator=validator,
        toc_classifier=toc_classifier,
        splitter=splitter,
        scorer=scorer,
    )


@lru_cache()
def get_pdf_loader() -> PDFDocumentLoader:
    # Initialize PDF document loader
    logger.info("Initializing PDF Document Loader")
    pdf_document_loader = PDFDocumentLoader()
    return pdf_document_loader


# ---- DB Lifecycle (Async) ----
async def get_db_connection() -> DBConnect:
    # Create and initialize database connection
    logger.info("Creating DB connection")
    settings = get_settings()
    conn = DBConnect(settings=settings)

    if hasattr(conn, "connect") and callable(conn.connect):
        result = conn.connect()
        if hasattr(result, "__await__"):
            await result
        else:
            await conn.connect()

    return conn

async def get_db_executor(conn: DBConnect) -> DBExecutor:
    # Create database executor bound to a connection
    logger.info("Creating DB executor")
    return DBExecutor(conn)

async def get_vector_extension(conn: DBConnect) -> VectorExtension:
    # Initialize vector extension for the database connection
    logger.info("Creating Vector Extension")
    vector_ext = VectorExtension(conn.conn)
    await vector_ext.enable()
    return vector_ext


# ---- DB Client (Per Request) ----
async def get_db_client() -> PostgresVectorClient:
    # Build fully initialized Postgres vector client per request
    logger.info("Creating PostgresVectorClient")

    conn = await get_db_connection()

    executor = DBExecutor(conn)
    vector_ext = await get_vector_extension(conn)

    client = PostgresVectorClient(
        conn=conn,
        db_executor=executor,
        vector_ext=vector_ext,
    )

    ok = await client.init()
    if not ok:
        raise RuntimeError("Failed to initialize PostgresVectorClient")

    return client


# ---- Retrievers (Factory Pattern) ----
def get_bm25_retriever(db_client: PostgresVectorClient) -> BM25Retriever:
    # Initialize BM25 retriever using database client
    logger.info("Initializing BM25 Retriever")
    return BM25Retriever(
        db_client=db_client,
        query_sql=BM25_SEARCH_QUERY,
    )


def get_vector_retriever(
    db_client: PostgresVectorClient,
    embedding_model: EmbedModelLoader,
) -> VectorRetriever:
    # Initialize vector retriever using embeddings
    logger.info("Initializing Vector Retriever")

    return VectorRetriever(
        db_client=db_client,
        embedding_fn=embedding_model,
        query_sql=VECTOR_SEARCH_QUERY,
    )


def get_hybrid_retriever(
    bm25: BM25Retriever,
    vector: VectorRetriever,
) -> HybridRetriever:
    # Combine BM25 and vector retrievers into hybrid strategy
    logger.info("Initializing Hybrid Retriever")

    return HybridRetriever(
        bm25=bm25,
        vector=vector,
    )


# ---- Optional Composition Helpers ----
def build_retrievers(
    db_client: PostgresVectorClient,
    embedding_model: EmbedModelLoader,
) -> dict[str, BM25Retriever | VectorRetriever | HybridRetriever]:
    # Construct all retriever variants in a single composition layer
    bm25 = get_bm25_retriever(db_client)
    vector = get_vector_retriever(db_client, embedding_model)

    hybrid = get_hybrid_retriever(bm25, vector)

    return {
        "bm25": bm25,
        "vector": vector,
        "hybrid": hybrid,
    }