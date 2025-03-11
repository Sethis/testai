

from typing import Optional

from dataclasses import dataclass

from testai.src.interactors.database.gateways.user import BaseUserGateWay, UserDomain


@dataclass(slots=True, kw_only=True, frozen=True)
class Assistant:
    id: int
    user_id: int

    openai_id: str
    name: str


@dataclass(slots=True, kw_only=True, frozen=True)
class Mental:
    id: int
    user_id: int

    temperament: str
    profession: str


@dataclass(slots=True, kw_only=True, frozen=True)
class User:
    id: int
    tg_id: int

    assistants: Optional[list[Assistant]] = None
    mental: Optional[Mental] = None


class UserRepo:
    __slots__ = ("_user_gateway", )

    def __init__(self, user_gateway: BaseUserGateWay):
        self._user_gateway = user_gateway

    @staticmethod
    def _build_user_model(
            user_domain: UserDomain
    ) -> User:
        mental = None
        if user_domain.mental is not None:
            mental = Mental(
                id=user_domain.mental.id,
                user_id=user_domain.mental.user_id,
                temperament=user_domain.mental.temperament,
                profession=user_domain.mental.profession
            )

        assistants = None
        if user_domain.assistans is not None:
            assistants = [
                Assistant(
                    id=value.id,
                    openai_id=value.openai_id,
                    user_id=value.user_id,
                    name=value.name
                ) for value in user_domain.assistans
            ]

        return User(
            id=user_domain.id,
            tg_id=user_domain.tg_id,
            assistants=assistants,
            mental=mental
        )

    async def get_user_by_tg_id(self, user_tg_id: int) -> User:
        user = await self._user_gateway.get_user_by_tg_id(user_tg_id)

        return self._build_user_model(user)

    async def get_user_by_id(self, user_id: int) -> User:
        user = await self._user_gateway.get_user_by_id(user_id)

        return self._build_user_model(user)

    async def get_user_by_tg_id_unsafe(self, tg_id: int) -> Optional[User]:
        user = await self._user_gateway.get_user_unsafe(tg_id=tg_id)

        if not user:
            return None

        return self._build_user_model(user)

    async def add_assistant(self, user_id: int, openai_id: str, name: str) -> User:
        await self._user_gateway.add_user_assistants(
            user_id=user_id,
            assistant_id=openai_id,
            assistant_name=name
        )

        await self._user_gateway.commit()

        return await self.get_user_by_id(user_id=user_id)

    async def upsert_user_mental(self, user_id: int, temperament: str, profession: str) -> User:
        await self._user_gateway.upsert_user_mental(
            user_id=user_id,
            temperament=temperament,
            profession=profession
        )

        await self._user_gateway.commit()

        return await self.get_user_by_id(user_id=user_id)

    async def upsert_user(self, tg_id: int) -> User:
        user = await self._user_gateway.upsert_user(
            tg_id=tg_id,
        )

        await self._user_gateway.commit()

        return self._build_user_model(user)
