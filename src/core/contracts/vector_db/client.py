# ---- Imports ----
from abc import ABC, abstractmethod
from typing import Any


# ---- Vector DB Client Contract ----
class VectorDBClientContract(ABC):

    # ---- Initialization ----
    @abstractmethod
    async def init(self) -> bool:
        pass

    # ---- System Readiness ----
    @abstractmethod
    async def is_system_ready(self) -> bool:
        pass

    # ---- Close Connection ----
    @abstractmethod
    async def close(self) -> None:
        pass

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