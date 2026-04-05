# ---- Imports ----
from abc import ABC, abstractmethod


# ---- DB Executor Contract ----
class DBExecutorContract(ABC):

    # ---- Execute Query ----
    @abstractmethod
    async def execute(
        self,
        query: str,
        params: tuple | None = None,
        fetch: bool = False
    ) -> list[tuple] | None:
        pass

    # ---- Execute One ----
    @abstractmethod
    async def execute_one(
        self,
        query: str,
        params: tuple | None = None
    ) -> tuple | None:
        pass

    # ---- Commit ----
    @abstractmethod
    async def commit(self) -> None:
        pass