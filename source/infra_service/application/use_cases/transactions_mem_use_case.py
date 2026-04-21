# ---- Imports ----
import logging
import asyncio


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Transactions Use Case ----
class TransactionsUseCase:

    def __init__(self, db_client, queries):
        self.db = db_client
        self.q = queries

    # ---- INIT ----
    async def init(self) -> bool:
        logger.info("[Transactions Use Case] initializing...")

        try:
            table_exists = await self.db.execute_one(self.q.HEALTH_CHECK)

            if table_exists and table_exists.get("to_regclass"):
                logger.info("[Transactions Use Case] already initialized")
                return True

            async with self.db:
                await self.db.execute(self.q.CREATE_TABLE)
                await self.db.execute(self.q.CREATE_USER_TIME_INDEX)
                await self.db.execute(self.q.CREATE_CATEGORY_INDEX)
                await self.db.execute(self.q.CREATE_PRODUCT_INDEX)
                await self.db.execute(self.q.CREATE_VECTOR_INDEX)

            await self.db.commit()

            logger.info("[Transactions Use Case] init success")
            return False

        except Exception as e:
            logger.exception("[Transactions Use Case] init failed")
            raise RuntimeError("Failed to initialize transactions_table") from e

    # ---- INSERT EVENT ----
    async def log_event(self, data: tuple) -> bool:
        logger.info("[Transactions Use Case] insert transaction event start")

        try:
            if not data:
                raise ValueError("invalid transaction payload")

            async with self.db:
                await self.db.execute(self.q.INSERT_EVENT, data)

            await self.db.commit()

            logger.info("[Transactions Use Case] insert transaction event success")
            return True

        except Exception as e:
            logger.exception("[Transactions Use Case] insert transaction event failed")
            raise RuntimeError("Failed to insert transaction") from e

    # ---- BM25 SEARCH ----
    async def bm25_search(self, user_id: str, session_id: str, query: str, limit: int = 10):
        logger.info("[Transactions Use Case] bm25 search start")

        try:
            if not user_id or not session_id or not query:
                raise ValueError("invalid bm25 input")

            return await self.db.execute(
                self.q.BM25_SEARCH,
                (user_id, session_id, query, query, limit),
                fetch=True,
            )

        except Exception as e:
            logger.exception("[Transactions Use Case] bm25 search failed")
            raise RuntimeError("BM25 search failed") from e

    # ---- VECTOR SEARCH ----
    async def vector_search(self, user_id: str, session_id: str, embedding, limit: int = 10):
        logger.info("[Transactions Use Case] vector search start")

        try:
            if not user_id or not session_id or embedding is None:
                raise ValueError("embedding and session_id are required")

            return await self.db.execute(
                self.q.VECTOR_SEARCH,
                (embedding, user_id, session_id, embedding, limit),
                fetch=True,
            )

        except Exception as e:
            logger.exception("[Transactions Use Case] vector search failed")
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
        logger.info("[Transactions Use Case] hybrid search start")

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
            logger.exception("[Transactions Use Case] hybrid search failed")
            raise RuntimeError("Hybrid search failed") from e

    # ---- COUNT ROWS (NEW - uses COUNT_ROWS query) ----
    async def count_rows(self) -> int:
        logger.info("[Transactions Use Case] count rows start")

        try:
            result = await self.db.execute_one(self.q.COUNT_ROWS)
            return result.get("total", 0) if result else 0

        except Exception as e:
            logger.exception("[Transactions Use Case] count rows failed")
            raise RuntimeError("Failed to count transactions") from e

    # ---- DELETE ALL ----
    async def delete_all(self) -> bool:
        logger.info("[Transactions Use Case] delete all start")

        try:
            # Check if table exists first
            table_exists = await self.db.execute_one(self.q.HEALTH_CHECK)
            if not table_exists or not table_exists.get("to_regclass"):
                logger.info("[Transactions Use Case] delete all skipped - table does not exist")
                return False

            count = await self.count_rows()
            if count == 0:
                logger.info("[Transactions Use Case] delete all skipped - table already empty")
                return False

            async with self.db:
                await self.db.execute(self.q.DELETE_ALL)

            await self.db.commit()

            logger.info("[Transactions Use Case] delete all success")
            return True

        except Exception as e:
            logger.exception("[Transactions Use Case] delete all failed")
            raise RuntimeError("Failed to delete all transactions") from e

    # ---- DROP TABLE ----
    async def drop_table(self) -> bool:
        logger.info("[Transactions Use Case] drop table start")

        try:
            table_exists = await self.db.execute_one(self.q.HEALTH_CHECK)

            if not table_exists or not table_exists.get("to_regclass"):
                logger.info("[Transactions Use Case] table does not exist")
                return False

            async with self.db:
                await self.db.execute(self.q.DROP_TABLE)

            await self.db.commit()

            logger.info("[Transactions Use Case] drop table success")
            return True

        except Exception as e:
            logger.exception("[Transactions Use Case] drop table failed")
            raise RuntimeError("Failed to drop transactions_table") from e

    # ---- NORMALIZE BM25 ----
    def _normalize_bm25(self, rows):
        out = []

        for r in rows or []:
            if isinstance(r, (tuple, list)):
                out.append({
                    "id": r[0],
                    "user_id": r[1],
                    "product": r[2],
                    "category": r[3],
                    "amount": r[4],
                    "quantity": r[5],
                    "currency": r[6],
                    "note": r[7],
                    "raw_input": r[8],
                    "created_at": r[9],
                    "bm25_score": float(r[10]) if len(r) > 10 else 0.0,
                    "vector_score": 0.0,
                })
            else:
                out.append({
                    "id": r.get("id"),
                    "user_id": r.get("user_id"),
                    "product": r.get("product"),
                    "category": r.get("category"),
                    "amount": r.get("amount"),
                    "quantity": r.get("quantity"),
                    "currency": r.get("currency"),
                    "note": r.get("note"),
                    "raw_input": r.get("raw_input"),
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
                    "product": r[2],
                    "category": r[3],
                    "amount": r[4],
                    "quantity": r[5],
                    "currency": r[6],
                    "note": r[7],
                    "raw_input": r[8],
                    "created_at": r[9],
                    "vector_score": float(r[10]) if len(r) > 10 else 0.0,
                    "bm25_score": 0.0,
                })
            else:
                out.append({
                    "id": r.get("id"),
                    "user_id": r.get("user_id"),
                    "product": r.get("product"),
                    "category": r.get("category"),
                    "amount": r.get("amount"),
                    "quantity": r.get("quantity"),
                    "currency": r.get("currency"),
                    "note": r.get("note"),
                    "raw_input": r.get("raw_input"),
                    "created_at": r.get("created_at"),
                    "vector_score": float(r.get("vector_score", 0.0)),
                    "bm25_score": 0.0,
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