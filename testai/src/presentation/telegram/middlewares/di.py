

from typing import Callable, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from openai import AsyncClient

from testai.src.interactors.database.gateways.user import FakeUserGateWay
from testai.src.interactors.database.repositories.user import UserRepo
from testai.src.interactors.processing.text_to_response import AssistantTextToResponseInteractor
from testai.src.interactors.processing.audio_to_text import WhisperAudioToTextInteractor
from testai.src.interactors.processing.text_to_audio import TTSTextToAudio


class DIMiddleware(BaseMiddleware):
    __slots__ = ("_client", )

    def __init__(self, client: AsyncClient):
        self._client = client

        self._user_repo = UserRepo(
            user_gateway=FakeUserGateWay()
        )
        self._text_to_response = AssistantTextToResponseInteractor(client=self._client)
        self._text_to_audio = TTSTextToAudio(client=self._client)
        self._audio_to_text = WhisperAudioToTextInteractor(client=self._client)

    async def __call__(
            self,
            handler: Callable,
            event: TelegramObject,
            data: dict[str, Any],
    ) -> None:

        data["user_repo"] = self._user_repo
        data["text_to_response"] = self._text_to_response
        data["text_to_audio"] = self._text_to_audio
        data["audio_to_text"] = self._audio_to_text

        await handler(event, data)
