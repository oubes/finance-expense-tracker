# ---- Imports ----
import logging


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

    # ---- ADD MESSAGE ----
    async def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        embedding=None,
    ) -> bool:
        try:
            if not user_id or not content:
                raise ValueError("Invalid input for memory insert")

            await self.db.execute(
                self.q.INSERT_MESSAGE,
                (user_id, role, content, embedding),
            )
            await self.db.commit()
            return True

        except Exception:
            logger.exception("[Semantic Memory Use Case] add_message failed")
            return False

    # ---- USER HISTORY ----
    async def get_user_history(self, user_id: str):
        try:
            if not user_id:
                raise ValueError("Invalid user_id")

            return await self.db.execute(
                self.q.GET_USER_HISTORY,
                (user_id,),
                fetch=True,
            )

        except Exception:
            logger.exception("[Semantic Memory Use Case] get_user_history failed")
            return []

    # ---- STM (RECENT MEMORY) ----
    async def get_stm(self, user_id: str, limit: int = 10):
        try:
            if limit <= 0:
                raise ValueError("limit must be > 0")

            return await self.db.execute(
                self.q.GET_STM,
                (user_id, limit),
                fetch=True,
            )

        except Exception:
            logger.exception("[Semantic Memory Use Case] get_stm failed")
            return []

    # ---- BM25 SEARCH ----
    async def bm25_search(self, user_id: str, query: str, limit: int = 10):
        try:
            if not user_id or not query:
                raise ValueError("Invalid bm25 input")

            return await self.db.execute(
                self.q.BM25_SEARCH,
                (user_id, query, query, limit),
                fetch=True,
            )

        except Exception:
            logger.exception("[Semantic Memory Use Case] bm25_search failed")
            return []

    # ---- VECTOR SEARCH ----
    async def vector_search(self, user_id: str, embedding, limit: int = 10) -> list:
        try:
            if embedding is None:
                raise ValueError("embedding is required")

            return await self.db.execute(
                self.q.VECTOR_SEARCH,
                (embedding, user_id, embedding, limit),
                fetch=True,
            )

        except Exception:
            logger.exception("[Semantic Memory Use Case] vector_search failed")
            return []

    # ---- HYBRID SEARCH ----
    async def hybrid_search(
        self,
        user_id: str,
        query: str,
        embedding,
        limit: int = 10,
        weights: dict = {
            "bm25": 0.4,
            "vector": 0.6,
        },
    ):
        try:
            if not user_id or not query:
                raise ValueError("Invalid hybrid input")

            weights = weights or {
                "bm25": 0.4,
                "vector": 0.6,
            }

            # ---- parallel retrieval ----
            bm25_task = self.bm25_search(user_id, query, limit * 2)
            vector_task = self.vector_search(user_id, embedding, limit * 2)

            bm25, vector = await bm25_task, await vector_task

            # ---- SAFE GUARD ----
            bm25 = bm25 or []
            vector = vector or []

            bm25 = self._normalize_bm25(bm25)
            vector = self._normalize_vector(vector)

            merged = self._merge(bm25, vector, weights)

            results = sorted(
                merged.values(),
                key=lambda x: x.get("score", 0.0),
                reverse=True,
            )

            return results[:limit]

        except Exception:
            logger.exception("[Semantic Memory Use Case] hybrid_search failed")
            return []

    # ---- NORMALIZE BM25 (tuple + dict safe) ----
    def _normalize_bm25(self, rows):
        out = []

        for r in rows or []:

            # ---- tuple / list format ----
            if isinstance(r, (tuple, list)):
                out.append({
                    "id": r[0],
                    "user_id": r[1] if len(r) > 1 else None,
                    "role": r[2] if len(r) > 2 else None,
                    "content": r[3] if len(r) > 3 else None,
                    "created_at": r[4] if len(r) > 4 else None,
                    "bm25_score": float(r[5]) if len(r) > 5 and r[5] is not None else 0.0,
                    "vector_score": 0.0,
                })
                continue

            # ---- dict format ----
            doc_id = r.get("id")
            if not doc_id:
                continue

            out.append({
                "id": doc_id,
                "user_id": r.get("user_id"),
                "role": r.get("role"),
                "content": r.get("content"),
                "created_at": r.get("created_at"),
                "bm25_score": float(r.get("bm25_score", 0.0)),
                "vector_score": 0.0,
            })

        return out

    # ---- NORMALIZE VECTOR (tuple + dict safe) ----
    def _normalize_vector(self, rows):
        out = []

        for r in rows or []:

            # ---- tuple / list format ----
            if isinstance(r, (tuple, list)):
                out.append({
                    "id": r[0],
                    "user_id": r[1] if len(r) > 1 else None,
                    "role": r[2] if len(r) > 2 else None,
                    "content": r[3] if len(r) > 3 else None,
                    "created_at": r[4] if len(r) > 4 else None,
                    "bm25_score": 0.0,
                    "vector_score": float(r[5]) if len(r) > 5 and r[5] is not None else 0.0,
                })
                continue

            # ---- dict format ----
            doc_id = r.get("id")
            if not doc_id:
                continue

            out.append({
                "id": doc_id,
                "user_id": r.get("user_id"),
                "role": r.get("role"),
                "content": r.get("content"),
                "created_at": r.get("created_at"),
                "bm25_score": 0.0,
                "vector_score": float(r.get("vector_score", 0.0)),
            })

        return out

    # ---- MERGE + SCORING ----
    def _merge(self, bm25, vector, weights):
        index = {}

        bm25_w = float(weights.get("bm25", 0.4))
        vec_w = float(weights.get("vector", 0.6))

        # ---- BM25 base ----
        for r in bm25:
            doc_id = r["id"]

            index[doc_id] = {
                **r,
                "score": float(r.get("bm25_score", 0.0)) * bm25_w,
                "vector_score": 0.0,
            }

        # ---- VECTOR fusion ----
        for r in vector:
            doc_id = r["id"]
            vec_score = float(r.get("vector_score", 0.0))

            if doc_id in index:
                index[doc_id]["vector_score"] = vec_score
                index[doc_id]["score"] += vec_score * vec_w
            else:
                index[doc_id] = {
                    **r,
                    "bm25_score": 0.0,
                    "vector_score": vec_score,
                    "score": vec_score * vec_w,
                }

        return index

    # ---- COUNT ----
    async def count(self) -> int:
        try:
            row = await self.db.execute_one(self.q.COUNT_ROWS)
            return row["total"] if row else 0

        except Exception:
            logger.exception("[Semantic Memory Use Case] count failed")
            return 0