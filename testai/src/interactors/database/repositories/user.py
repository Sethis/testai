

from dataclasses import dataclass

from testai.src.interactors.database.gateways.user import UserGateWay


@dataclass(slots=True, kw_only=True, frozen=True)
class Assistant:
    id: str
    name: str


@dataclass(slots=True, kw_only=True, frozen=True)
class User:
    id: int
    tg_id: int
    assistants: list[Assistant]


class UserRepo:
    __slots__ = ("_user_gateway", )

    def __init__(self, user_gateway: UserGateWay):
        self._user_gateway = user_gateway

    @staticmethod
    def _build_user_model(
            user_id: int,
            user_tg_id: int,
            user_assistance: list[tuple[str, str]]
    ) -> User:
        assistants = [
            Assistant(id=assistant[0], name=assistant[1]) for assistant in user_assistance
        ]

        return User(
            id=user_id,
            tg_id=user_tg_id,
            assistants=assistants
        )

    async def get_user_by_tg_id(self, user_tg_id: int) -> User:
        user_id, tg_id = await self._user_gateway.get_user_by_tg_id(tg_id=user_tg_id)

        user_assistance = await self._user_gateway.get_user_assistants_ids(
            user_id=user_id
        )

        return self._build_user_model(
            user_id=user_id,
            user_tg_id=tg_id,
            user_assistance=user_assistance
        )

    async def get_user_by_id(self, user_id: int) -> User:
        user_id, tg_id = await self._user_gateway.get_user_by_id(user_id=user_id)

        user_assistance = await self._user_gateway.get_user_assistants_ids(
            user_id=user_id
        )

        return self._build_user_model(
            user_id=user_id,
            user_tg_id=tg_id,
            user_assistance=user_assistance
        )

    async def add_assistant(self, user_id: int, assistant_id: str, name: str) -> User:
        await self._user_gateway.add_user_assistants(
            user_id=user_id,
            assistant_id=assistant_id,
            assistant_name=name
        )

        await self._user_gateway.commit()

        return await self.get_user_by_id(user_id=user_id)
