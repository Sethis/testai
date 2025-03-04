

from typing import Awaitable
from abc import ABC, abstractmethod
from collections import defaultdict


class UserGateWay(ABC):
    @abstractmethod
    async def get_user_by_tg_id(self, tg_id: int) -> tuple[int, int]:
        raise NotImplementedError()

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> tuple[int, int]:
        raise NotImplementedError()

    @abstractmethod
    async def get_user_assistants_ids(self, user_id: int) -> list[tuple[str, str]]:
        raise NotImplementedError()

    @abstractmethod
    async def add_user_assistants(self, user_id: int, assistant_id: str, assistant_name: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def commit(self):
        raise NotImplementedError()


class FakeUserGateWay(UserGateWay):
    __slots__ = ("_data", "_not_commited")

    def __init__(self):
        self._data = defaultdict(list)
        self._not_commited: list[Awaitable] = []

    async def get_user_assistants_ids(self, user_id: int) -> list[tuple[str, str]]:
        return self._data[user_id]

    async def get_user_by_tg_id(self, tg_id: int) -> tuple[int, int]:
        return tg_id, tg_id

    async def get_user_by_id(self, user_id: int) -> tuple[int, int]:
        return user_id, user_id

    async def add_user_assistants(self, user_id: int, assistant_id: str, assistant_name: str) -> None:
        async def uncommited():
            data = self._data[user_id]

            data.append(
                (assistant_id, assistant_name)
            )

            self._data[user_id] = data

        self._not_commited.append(uncommited())

    async def commit(self):
        for func in self._not_commited:
            await func

        self._not_commited = []
