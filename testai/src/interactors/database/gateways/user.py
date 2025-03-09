

from typing import Awaitable, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from testai.src.interactors.database.structures import User, Mental, Assisstant


@dataclass(slots=True, kw_only=True)
class AssisstantDomain:
    id: int
    user_id: int

    openai_id: str
    name: str


@dataclass(slots=True, kw_only=True)
class MentalDataDomain:
    id: int
    user_id: int

    temperament: str
    profession: str


@dataclass(slots=True, kw_only=True)
class UserDomain:
    id: int
    tg_id: int

    assistans: Optional[list[AssisstantDomain]] = None
    mental: Optional[MentalDataDomain] = None


class BaseUserGateWay(ABC):
    @abstractmethod
    async def get_user_by_tg_id(self, tg_id: int) -> UserDomain:
        raise NotImplementedError()

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> UserDomain:
        raise NotImplementedError()

    @abstractmethod
    async def get_user_unsafe(self, tg_id: int) -> Optional[UserDomain]:
        raise NotImplementedError()

    @abstractmethod
    async def get_user_assistants(self, user_id: int) -> list[AssisstantDomain]:
        raise NotImplementedError()

    @abstractmethod
    async def add_user_assistants(self, user_id: int, assistant_id: str, assistant_name: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def upsert_user(self, tg_id: int) -> UserDomain:
        raise NotImplementedError()

    @abstractmethod
    async def upsert_user_mental(self, user_id: int, temperament: str, profession: str) -> Mental:
        raise NotImplementedError()

    @abstractmethod
    async def commit(self):
        raise NotImplementedError()


class FakeUserGateWay(BaseUserGateWay):
    __slots__ = ("_not_commited", "_users")

    def __init__(self):
        self._users: dict[int, UserDomain] = {}
        self._not_commited: list[Awaitable] = []

    async def get_user_by_tg_id(self, tg_id: int) -> UserDomain:
        for i in self._users.values():
            if i.tg_id == tg_id:
                return i

        raise ValueError("Undefined user")

    async def get_user_by_id(self, user_id: int) -> UserDomain:
        if self._users.get(user_id, None):
            return self._users[user_id]

        raise ValueError("Undefined user")

    async def get_user_assistants(self, user_id: int) -> list[AssisstantDomain]:
        return self._users[user_id].assistans

    async def add_user_assistants(self, user_id: int, assistant_id: str, assistant_name: str) -> None:
        user = self._users[user_id]

        user.assistans.append(AssisstantDomain(id=1, openai_id=assistant_id, name=assistant_name, user_id=user_id))

    async def upsert_user(self, tg_id: int) -> UserDomain:
        if self._users.get(tg_id, None):
            self._users[tg_id] = UserDomain(id=tg_id, tg_id=tg_id, assistans=[])

        return self._users[tg_id]

    async def upsert_user_mental(self, user_id: int, temperament: str, profession: str) -> MentalDataDomain:
        mental = MentalDataDomain(
            id=1, user_id=user_id, temperament=temperament, profession=profession
        )

        self._users[user_id].mental = mental

        return mental

    async def get_user_unsafe(self, tg_id: int) -> Optional[UserDomain]:
        for i in self._users.values():
            if i.tg_id == tg_id:
                return i

        return None

    async def commit(self):
        for func in self._not_commited:
            await func

        self._not_commited = []


class UserGateWay(BaseUserGateWay):
    __slots__ = ("_session", )

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_user_by_tg_id(self, tg_id: int) -> UserDomain:
        stmt = select(User).where(User.tg_id == tg_id).options(
            joinedload(User.assisstants),
            joinedload(User.mental)
        )

        result = await self._session.scalar(stmt)

        return UserDomain(
            id=result.id,
            tg_id=result.tg_id,
            assistans=result.assisstants,
            mental=result.mental
        )

    async def get_user_by_id(self, user_id: int) -> UserDomain:
        stmt = select(User).where(User.id == user_id).options(
            joinedload(User.assisstants),
            joinedload(User.mental)
        )

        result = await self._session.scalar(stmt)

        return UserDomain(
            id=result.id,
            tg_id=result.tg_id,
            assistans=result.assisstants,
            mental=result.mental
        )

    async def get_user_unsafe(self, tg_id: int) -> Optional[UserDomain]:
        stmt = select(User).where(User.tg_id == tg_id).options(
            joinedload(User.assisstants),
            joinedload(User.mental)
        )

        result = await self._session.scalar(stmt)

        if not result:
            return None

        return UserDomain(
            id=result.id,
            tg_id=result.tg_id,
            assistans=result.assisstants,
            mental=result.mental
        )

    async def get_user_assistants(self, user_id: int) -> list[AssisstantDomain]:
        stmt = select(Assisstant).where(Assisstant.user_id == user_id).options()

        result = await self._session.scalars(stmt)

        return [
            AssisstantDomain(
                id=value.id,
                openai_id=value.openai_id,
                name=value.name,
                user_id=value.user_id
            ) for value in result
        ]

    async def add_user_assistants(self, user_id: int, assistant_id: str, assistant_name: str) -> None:
        stmt = insert(Assisstant).values(user_id=user_id, openai_id=assistant_id, name=assistant_name)

        await self._session.execute(stmt)

    async def upsert_user(self, tg_id: int) -> UserDomain:
        # since we have only one argument, do_update is not needed
        stmt = insert(User).values(tg_id=tg_id).on_conflict_do_update(
            index_elements=[User.id],
            set_={
                "tg_id": tg_id
            }
        ).returning(User)

        user = await self._session.scalar(stmt)

        return UserDomain(
            id=user.id,
            tg_id=user.tg_id
        )

    async def upsert_user_mental(self, user_id: int, temperament: str, profession: str) -> MentalDataDomain:
        stmt = insert(Mental).values(
            user_id=user_id,
            temperament=temperament,
            profession=profession
        ).on_conflict_do_update(
            index_elements=[Mental.user_id],
            set_={
                "temperament": temperament,
                "profession": profession
            }
        ).returning(Mental)

        mental = await self._session.scalar(stmt)

        return MentalDataDomain(
            id=mental.id,
            user_id=mental.user_id,
            temperament=mental.temperament,
            profession=mental.profession
        )

    async def commit(self) -> None:
        await self._session.commit()
