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
            await self.db.execute(self.q.CREATE_TABLE)
            await self.db.execute(self.q.CREATE_INDEX)
            await self.db.commit()
            return True

        except Exception:
            logger.exception("[Semantic Memory Use Case] init failed")
            return False

    # ---- HEALTH CHECK ----
    async def health(self) -> bool:
        logger.info("[Semantic Memory Use Case] health check start")

        try:
            row = await self.db.execute_one(self.q.HEALTH_CHECK)
            return bool(row and row.get("to_regclass"))

        except Exception:
            logger.exception("[Semantic Memory Use Case] health failed")
            return False

    # ---- ADD MESSAGE ----
    async def add_message(self, user_id: str, role: str, content: str, embedding=None) -> bool:
        try:
            if not user_id or not content:
                raise ValueError("invalid input")

            await self.db.execute(
                self.q.INSERT_MESSAGE,
                (user_id, role, content, embedding),
            )
            await self.db.commit()
            return True

        except Exception:
            logger.exception("[Semantic Memory Use Case] add_message failed")
            return False

    # ---- DELETE ALL ----
    async def delete_all(self) -> bool:
        logger.info("[Semantic Memory Use Case] delete all start")

        try:
            await self.db.execute(self.q.DELETE_ALL)
            await self.db.commit()
            return True

        except Exception:
            logger.exception("[Semantic Memory Use Case] delete_all failed")
            return False

    # ---- DROP TABLE ----
    async def drop_table(self) -> bool:
        logger.info("[Semantic Memory Use Case] drop table start")

        try:
            await self.db.execute(self.q.DROP_TABLE)
            await self.db.commit()
            return True

        except Exception:
            logger.exception("[Semantic Memory Use Case] drop_table failed")
            return False

    # ---- COUNT ----
    async def count(self) -> int:
        logger.info("[Semantic Memory Use Case] count start")

        try:
            row = await self.db.execute_one(self.q.COUNT_ROWS)
            return row["total"] if row else 0

        except Exception:
            logger.exception("[Semantic Memory Use Case] count failed")
            return 0

    # ---- HISTORY ----
    async def get_user_history(self, user_id: str):
        try:
            if not user_id:
                raise ValueError("invalid user_id")

            return await self.db.execute(
                self.q.GET_USER_HISTORY,
                (user_id,),
                fetch=True,
            )

        except Exception:
            logger.exception("[Semantic Memory Use Case] history failed")
            return []

    # ---- STM ----
    async def get_stm(self, user_id: str, limit: int = 10):
        try:
            return await self.db.execute(
                self.q.GET_STM,
                (user_id, limit),
                fetch=True,
            )

        except Exception:
            logger.exception("[Semantic Memory Use Case] stm failed")
            return []

    # ---- BM25 SEARCH ----
    async def bm25_search(self, user_id: str, query: str, limit: int = 10):
        try:
            if not user_id or not query:
                raise ValueError("invalid bm25 input")

            return await self.db.execute(
                self.q.BM25_SEARCH,
                (user_id, query, query, limit),
                fetch=True,
            )

        except Exception:
            logger.exception("[Semantic Memory Use Case] bm25 failed")
            return []

    # ---- VECTOR SEARCH ----
    async def vector_search(self, user_id: str, embedding, limit: int = 10):
        try:
            if embedding is None:
                raise ValueError("embedding required")

            return await self.db.execute(
                self.q.VECTOR_SEARCH,
                (embedding, user_id, embedding, limit),
                fetch=True,
            )

        except Exception:
            logger.exception("[Semantic Memory Use Case] vector failed")
            return []

    # ---- HYBRID SEARCH ----
    async def hybrid_search(
        self,
        user_id: str,
        query: str,
        embedding,
        limit: int = 10,
        weights: dict = {"bm25": 0.4, "vector": 0.6},
    ):
        try:
            if not user_id or not query or embedding is None:
                raise ValueError("invalid hybrid input")

            weights = weights or {"bm25": 0.4, "vector": 0.6}

            bm25_task = self.bm25_search(user_id, query, limit * 2)
            vector_task = self.vector_search(user_id, embedding, limit * 2)

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

        except Exception:
            logger.exception("[Semantic Memory Use Case] hybrid failed")
            return []

    # ---- NORMALIZE BM25 ----
    def _normalize_bm25(self, rows):
        out = []

        for r in rows or []:
            if isinstance(r, (tuple, list)):
                out.append({
                    "id": r[0],
                    "user_id": r[1],
                    "role": r[2],
                    "content": r[3],
                    "created_at": r[4],
                    "bm25_score": float(r[5]) if len(r) > 5 else 0.0,
                    "vector_score": 0.0,
                })
            else:
                out.append({
                    "id": r.get("id"),
                    "user_id": r.get("user_id"),
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
                    "role": r[2],
                    "content": r[3],
                    "created_at": r[4],
                    "bm25_score": 0.0,
                    "vector_score": float(r[5]) if len(r) > 5 else 0.0,
                })
            else:
                out.append({
                    "id": r.get("id"),
                    "user_id": r.get("user_id"),
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
                "vector_score": 0.0,
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