# ---- Imports ----
import logging
from typing import Any


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Helpers ----
def _get(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _to_params(r: Any) -> tuple:
    return (
        _get(r, "id"),
        _get(r, "content"),
        _get(r, "summary"),
        _get(r, "embedding"),
        _get(r, "chunk_title"),
        _get(r, "doc_title"),
        _get(r, "source"),
        _get(r, "page"),
        _get(r, "total_pages"),
        _get(r, "created_at"),
        _get(r, "pipeline_version"),
        _get(r, "score"),
    )


# ---- Chunking Use Case ----
class ChunkingUseCase:

    def __init__(self, client, queries, settings):
        self.db = client
        self.q = queries
        self.settings = settings

    # ---- INIT ----
    async def init(self) -> bool:
        logger.info("[Chunking Use Case] initializing...")

        try:
            table_exists = await self.db.execute_one(self.q.TABLE_EXISTS_SQL)

            if table_exists and table_exists.get("to_regclass"):
                logger.info("[Chunking Use Case] chunks_table already initialized")
                return True

            sql = self.q.CREATE_CHUNKS_TABLE_SQL.format(
                dim=self.settings.embeddings.dimension
            )

            async with self.db:
                await self.db.execute(sql)

            logger.info("[Chunking Use Case] init success")
            return False

        except Exception as e:
            logger.exception("[Chunking Use Case] init failed")
            raise RuntimeError("Failed to initialize chunks_table") from e

    # ---- HEALTH CHECK ----
    async def health(self):
        logger.info("[Chunking Use Case] health check start")

        try:
            table_exists = await self.db.execute_one(self.q.TABLE_EXISTS_SQL)

            if table_exists and table_exists.get("to_regclass"):
                logger.info("[Chunking Use Case] health check completed successfully")
                return True

            return False

        except Exception as e:
            logger.exception("[Chunking Use Case] health check failed")
            raise RuntimeError(
                "[Chunking Use Case] Chunks_table health check failed"
            ) from e

    # ---- UPSERT ----
    async def upsert(self, records: list[Any]) -> None:
        logger.info("[Chunking Use Case] upsert start")

        if not records:
            raise ValueError("records list is empty")

        try:
            params_list = [_to_params(r) for r in records]

            async with self.db:
                await self.db.executemany(
                    self.q.INSERT_CHUNK_SQL,
                    params_list
                )

            logger.info(
                f"[Chunking Use Case] upsert completed | count={len(records)}"
            )

        except Exception as e:
            logger.exception("[Chunking Use Case] upsert failed")
            raise RuntimeError(
                "[Chunking Use Case] Chunks_table upsert failed"
            ) from e

    # ---- DELETE ALL ----
    async def delete_all(self) -> None:
        logger.info("[Chunking Use Case] delete all start")

        try:
            async with self.db:
                await self.db.execute(self.q.DELETE_CHUNKS_SQL)

            logger.info("[Chunking Use Case] delete all success")

        except Exception as e:
            logger.exception("[Chunking Use Case] delete_all failed")
            raise RuntimeError(
                "[Chunking Use Case] Chunks_table delete_all failed"
            ) from e

    # ---- DROP TABLE ----
    async def drop_table(self) -> None:
        logger.info("[Chunking Use Case] drop table start")

        try:
            async with self.db:
                await self.db.execute(self.q.DROP_CHUNKS_TABLE_SQL)

            logger.info("[Chunking Use Case] drop table success")

        except Exception as e:
            logger.exception("[Chunking Use Case] drop_table failed")
            raise RuntimeError(
                "[Chunking Use Case] Chunks_table drop_table failed"
            ) from e

    # ---- COUNT ----
    async def count(self) -> int:
        logger.info("[Chunking Use Case] count start")

        try:
            row = await self.db.execute_one(self.q.COUNT_CHUNKS_SQL)

            if not row:
                return 0

            if isinstance(row, dict):
                return list(row.values())[0]

            return row[0]

        except Exception as e:
            logger.exception("[Chunking Use Case] count failed")
            raise RuntimeError("Chunk count failed") from e

    # ---- BM25 SEARCH ----
    async def bm25_search(self, query: str, limit: int = 10):
        logger.info("[Chunking Use Case] bm25 search start")

        try:
            if not query:
                raise ValueError("Invalid bm25 input")

            return await self.db.execute(
                self.q.BM25_SEARCH_SQL,
                (query, query, limit),
                fetch=True,
            )

        except Exception:
            logger.exception("[Chunking Use Case] bm25_search failed")
            return []

    # ---- VECTOR SEARCH ----
    async def vector_search(self, embedding, limit: int = 10):
        logger.info("[Chunking Use Case] vector search start")
        try:
            if embedding is None:
                raise ValueError("embedding required")

            # Ensure embedding is a string for pgvector
            if isinstance(embedding, list):
                embedding_str = str(embedding)
            else:
                embedding_str = embedding
            
            return await self.db.execute(
                self.q.VECTOR_SEARCH_SQL,
                (embedding_str, limit),
                fetch=True,
            )

        except Exception:
            logger.exception("[Chunking Use Case] vector_search failed")
            return []

    # ---- HYBRID SEARCH ----
    async def hybrid_search(
        self,
        query: str,
        embedding,
        limit: int = 10,
        weights: dict = {"bm25": 0.4, "vector": 0.6},
    ):
        logger.info("[Chunking Use Case] hybrid search start")

        try:
            bm25_task = self.bm25_search(query, limit * 2)
            vector_task = self.vector_search(embedding, limit * 2)

            bm25, vector = await bm25_task, await vector_task

            bm25 = self._normalize_bm25(bm25)
            vector = self._normalize_vector(vector)

            merged = self._merge(bm25, vector, weights)

            results = sorted(
                merged.values(),
                key=lambda x: x.get("vector_score", 0.0),
                reverse=True,
            )

            return results[:limit]

        except Exception:
            logger.exception("[Chunking Use Case] hybrid_search failed")
            return []

    # ---- NORMALIZE BM25 ----
    def _normalize_bm25(self, rows):
        out = []
        for row in rows or []:
            if isinstance(row, (tuple, list)):
                out.append({
                    "id": row[0],
                    "content": row[1],
                    "summary": row[2],
                    "chunk_title": row[3],
                    "doc_title": row[4],
                    "source": row[5],
                    "page": row[6],
                    "total_pages": row[7],
                    "created_at": row[8],
                    "pipeline_version": row[9],
                    "chunk_score": float(row[10]) if len(row) > 10 and row[10] is not None else 0.0,
                    "bm25_score": float(row[11] if len(row) > 11 else 0.0),
                    "vector_score": 0.0,
                })
                continue

            out.append({
                "id": row.get("id"),
                "content": row.get("content"),
                "summary": row.get("summary"),
                "chunk_title": row.get("chunk_title"),
                "doc_title": row.get("doc_title"),
                "source": row.get("source"),
                "page": row.get("page"),
                "total_pages": row.get("total_pages"),
                "created_at": row.get("created_at"),
                "pipeline_version": row.get("pipeline_version"),
                "chunk_score": row.get("score"),
                "bm25_score": float(row.get("bm25_score", 0.0)),
                "vector_score": 0.0,
            })
        return out

    # ---- NORMALIZE VECTOR ----
    def _normalize_vector(self, rows):
        out = []
        for row in rows or []:
            if isinstance(row, (tuple, list)):
                out.append({
                    "id": row[0],
                    "content": row[1],
                    "summary": row[2],
                    "chunk_title": row[3],
                    "doc_title": row[4],
                    "source": row[5],
                    "page": row[6],
                    "total_pages": row[7],
                    "created_at": row[8],
                    "pipeline_version": row[9],
                    "chunk_score": float(row[10]) if len(row) > 10 and row[10] is not None else 0.0,
                    "bm25_score": 0.0,
                    "vector_score": float(row[11] if len(row) > 11 else 0.0),
                })
                continue

            out.append({
                "id": row.get("id"),
                "content": row.get("content"),
                "summary": row.get("summary"),
                "chunk_title": row.get("chunk_title"),
                "doc_title": row.get("doc_title"),
                "source": row.get("source"),
                "page": row.get("page"),
                "total_pages": row.get("total_pages"),
                "created_at": row.get("created_at"),
                "pipeline_version": row.get("pipeline_version"),
                "chunk_score": row.get("score"),
                "bm25_score": 0.0,
                "vector_score": float(row.get("vector_score", 0.0)),
            })
        return out

    # ---- MERGE ----
    def _merge(self, bm25, vector, weights):
        index = {}

        bm25_w = float(weights.get("bm25", 0.4))
        vec_w = float(weights.get("vector", 0.6))

        for row in bm25:
            index[row["id"]] = {
                **row,
                "chunk_score": float(row["chunk_score"]) if row.get("chunk_score") is not None else 0.0,
                "bm25_score": float(row["bm25_score"]) if row.get("bm25_score") is not None else 0.0,
                "vector_score": float(row.get("vector_score", 0.0)) if row.get("vector_score") is not None else 0.0,
            }

        for row in vector:
            doc_id = row["id"]
            vec_score = float(row["vector_score"]) if row.get("vector_score") is not None else 0.0

            if doc_id in index:
                index[doc_id]["vector_score"] = vec_score
            else:
                index[doc_id] = {
                    **row,
                    "chunk_score": float(row["chunk_score"]) if row.get("chunk_score") is not None else 0.0,
                    "bm25_score": float(row.get("bm25_score", 0.0)) if row.get("bm25_score") is not None else 0.0,
                    "vector_score": vec_score,
                }

        return index