# ---- Imports ----
import logging
import asyncio


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Semantic Memory Use Case ----
class SemanticMemoryUseCase:

    def __init__(self, db_client, queries):
        self.db = db_client
        self.q = queries

    # ---- INIT ----
    async def init(self) -> bool:
        logger.info("[Semantic Memory Use Case] initializing...")

        try:
            table_exists = await self.db.execute_one(
                self.q.HEALTH_CHECK
            )

            if table_exists and table_exists.get("to_regclass"):
                logger.info("[Semantic Memory Use Case] semantic_memory already initialized")
                return True


            async with self.db:
                await self.db.execute(self.q.CREATE_TABLE)
                await self.db.execute(self.q.CREATE_VECTOR_INDEX_SQL)
                await self.db.execute(self.q.CREATE_FTS_INDEX_SQL)

            await self.db.commit()

            logger.info("[Semantic Memory Use Case] init success")
            return False

        except Exception as e:
            logger.exception("[Semantic Memory Use Case] init failed")
            raise RuntimeError("Failed to initialize semantic_memory") from e

    # ---- HEALTH CHECK ----
    async def health(self) -> bool:
        logger.info("[Semantic Memory Use Case] health check start")

        try:
            row = await self.db.execute_one(self.q.HEALTH_CHECK)
            return bool(row and row.get("to_regclass"))

        except Exception as e:
            logger.exception("[Semantic Memory Use Case] health failed")
            raise RuntimeError("Semantic memory health check failed") from e

    # ---- ADD MESSAGE ----
    async def add_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        embedding=None
    ) -> bool:
        logger.info("[Semantic Memory Use Case] add message start")

        try:
            if not user_id or not session_id or not content:
                raise ValueError("invalid input")

            async with self.db:
                await self.db.execute(
                    self.q.INSERT_MESSAGE,
                    (user_id, session_id, role, content, embedding),
                )

            await self.db.commit()
            return True

        except Exception as e:
            logger.exception("[Semantic Memory Use Case] add_message failed")
            raise RuntimeError("Failed to insert message") from e

    # ---- DELETE ALL ----
    async def delete_all(self) -> None:
        logger.info("[Semantic Memory Use Case] delete all start")

        try:
            async with self.db:
                await self.db.execute(self.q.DELETE_ALL)

            await self.db.commit()
            logger.info("[Semantic Memory Use Case] delete all success")

        except Exception as e:
            logger.exception("[Semantic Memory Use Case] delete_all failed")
            raise RuntimeError("Failed to delete memory") from e

    # ---- DROP TABLE ----
    async def drop_table(self) -> bool:
        logger.info("[Semantic Memory Use Case] drop table start")

        try:
            table_exists = await self.db.execute_one(
                self.q.HEALTH_CHECK
            )

            if not table_exists or not table_exists.get("to_regclass"):
                logger.info("[Semantic Memory Use Case] table does not exist")
                return False

            async with self.db:
                await self.db.execute(self.q.DROP_TABLE)

            await self.db.commit()

            logger.info("[Semantic Memory Use Case] drop table success")
            return True

        except Exception as e:
            logger.exception("[Semantic Memory Use Case] drop_table failed")
            raise RuntimeError("Failed to drop semantic_memory table") from e

    # ---- COUNT ----
    async def count(self) -> int:
        logger.info("[Semantic Memory Use Case] count start")

        try:
            row = await self.db.execute_one(self.q.COUNT_ROWS)
            return row["total"] if row else 0

        except Exception as e:
            logger.exception("[Semantic Memory Use Case] count failed")
            raise RuntimeError("Failed to count memory rows") from e

    # ---- HISTORY ----
    async def get_user_history(self, user_id: str, session_id: str):
        logger.info("[Semantic Memory Use Case] history start")

        try:
            if not user_id or not session_id:
                raise ValueError("invalid input")

            return await self.db.execute(
                self.q.GET_USER_HISTORY,
                (user_id, session_id),
                fetch=True,
            )

        except Exception as e:
            logger.exception("[Semantic Memory Use Case] history failed")
            raise RuntimeError("History fetch failed") from e

    # ---- STM ----
    async def get_stm(self, user_id: str, session_id: str, limit: int = 10):
        logger.info("[Semantic Memory Use Case] stm start")

        try:
            return await self.db.execute(
                self.q.GET_STM,
                (user_id, session_id, limit),
                fetch=True,
            )

        except Exception as e:
            logger.exception("[Semantic Memory Use Case] stm failed")
            raise RuntimeError("STM fetch failed") from e

    # ---- BM25 SEARCH ----
    async def bm25_search(self, user_id: str, session_id: str, query: str, limit: int = 10):
        logger.info("[Semantic Memory Use Case] bm25 search start")

        try:
            if not user_id or not session_id or not query:
                raise ValueError("invalid bm25 input")

            return await self.db.execute(
                self.q.BM25_SEARCH,
                (user_id, session_id, query, query, limit),
                fetch=True,
            )

        except Exception as e:
            logger.exception("[Semantic Memory Use Case] bm25 failed")
            raise RuntimeError("BM25 search failed") from e

    # ---- VECTOR SEARCH ----
    async def vector_search(self, user_id: str, session_id: str, embedding, limit: int = 10):
        logger.info("[Semantic Memory Use Case] vector search start")

        try:
            if embedding is None:
                raise ValueError("embedding required")

            return await self.db.execute(
                self.q.VECTOR_SEARCH,
                (embedding, user_id, session_id, embedding, limit),
                fetch=True,
            )

        except Exception as e:
            logger.exception("[Semantic Memory Use Case] vector failed")
            raise RuntimeError("Vector search failed") from e

    # ---- HYBRID SEARCH ----
    async def hybrid_search(
        self,
        user_id: str,
        session_id: str,
        query: str,
        embedding,
        limit: int = 10,
        weights: dict = {"bm25": 0.4, "vector": 0.6},
    ):
        logger.info("[Semantic Memory Use Case] hybrid search start")

        try:
            if not user_id or not session_id or not query or embedding is None:
                raise ValueError("invalid hybrid input")

            weights = weights or {"bm25": 0.4, "vector": 0.6}

            bm25_task = self.bm25_search(user_id, session_id, query, limit * 2)
            vector_task = self.vector_search(user_id, session_id, embedding, limit * 2)

            bm25, vector = await asyncio.gather(bm25_task, vector_task)

            bm25 = self._normalize_bm25(bm25 or [])
            vector = self._normalize_vector(vector or [])

            merged = self._merge(bm25, vector, weights)

            results = sorted(
                merged.values(),
                key=lambda x: x.get("score", 0.0),
                reverse=True,
            )

            return results[:limit]

        except Exception as e:
            logger.exception("[Semantic Memory Use Case] hybrid failed")
            raise RuntimeError("Hybrid search failed") from e

    # ---- NORMALIZE BM25 ----
    def _normalize_bm25(self, rows):
        out = []

        for r in rows or []:
            if isinstance(r, (tuple, list)):
                out.append({
                    "id": r[0],
                    "user_id": r[1],
                    "session_id": r[2],
                    "role": r[3],
                    "content": r[4],
                    "created_at": r[5],
                    "bm25_score": float(r[6]) if len(r) > 6 else 0.0,
                    "vector_score": 0.0,
                })
                continue

            out.append({
                "id": r.get("id"),
                "user_id": r.get("user_id"),
                "session_id": r.get("session_id"),
                "role": r.get("role"),
                "content": r.get("content"),
                "created_at": r.get("created_at"),
                "bm25_score": float(r.get("bm25_score", 0.0)),
                "vector_score": 0.0,
            })

        return out

    # ---- NORMALIZE VECTOR ----
    def _normalize_vector(self, rows):
        out = []

        for r in rows or []:
            if isinstance(r, (tuple, list)):
                out.append({
                    "id": r[0],
                    "user_id": r[1],
                    "session_id": r[2],
                    "role": r[3],
                    "content": r[4],
                    "created_at": r[5],
                    "bm25_score": 0.0,
                    "vector_score": float(r[6]) if len(r) > 6 else 0.0,
                })
                continue

            out.append({
                "id": r.get("id"),
                "user_id": r.get("user_id"),
                "session_id": r.get("session_id"),
                "role": r.get("role"),
                "content": r.get("content"),
                "created_at": r.get("created_at"),
                "bm25_score": 0.0,
                "vector_score": float(r.get("vector_score", 0.0)),
            })

        return out

    # ---- MERGE ----
    def _merge(self, bm25, vector, weights):
        index = {}

        bm25_w = float(weights.get("bm25", 0.4))
        vec_w = float(weights.get("vector", 0.6))

        for r in bm25:
            index[r["id"]] = {
                **r,
                "score": r["bm25_score"] * bm25_w,
            }

        for r in vector:
            doc_id = r["id"]
            vec_score = r["vector_score"]

            if doc_id in index:
                index[doc_id]["vector_score"] = vec_score
                index[doc_id]["score"] += vec_score * vec_w
            else:
                index[doc_id] = {
                    **r,
                    "score": vec_score * vec_w,
                }

        return index