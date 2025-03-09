

from typing import Callable, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from openai import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from testai.src.interactors.database.gateways.user import UserGateWay
from testai.src.interactors.database.repositories.user import UserRepo
from testai.src.interactors.processing.text_to_response import (
    AssistantTextToResponseInteractor,
    CompletitionsBasedConfirmTextFormat,
    AssistantFunctionInteractor
)
from testai.src.interactors.processing.audio_to_text import WhisperAudioToTextInteractor
from testai.src.interactors.processing.text_to_audio import TTSTextToAudio


class DIMiddleware(BaseMiddleware):
    __slots__ = (
        "_client",
        "_text_to_response",
        "_text_to_audio",
        "_audio_to_text",
        "_confirm_text",
        "_context_based_assistant",
        "_sessionmaker"
    )

    def __init__(self, client: AsyncClient, sessionmaker: async_sessionmaker):
        self._client = client
        self._text_to_response = AssistantTextToResponseInteractor(client=self._client)
        self._text_to_audio = TTSTextToAudio(client=self._client)
        self._audio_to_text = WhisperAudioToTextInteractor(client=self._client)
        self._confirm_text = CompletitionsBasedConfirmTextFormat(client=self._client)
        self._context_based_assistant = AssistantFunctionInteractor(client=self._client)
        self._sessionmaker = sessionmaker

    async def __call__(
            self,
            handler: Callable,
            event: TelegramObject,
            data: dict[str, Any],
    ) -> None:

        data["text_to_response"] = self._text_to_response
        data["text_to_audio"] = self._text_to_audio
        data["audio_to_text"] = self._audio_to_text
        data["confirm_text"] = self._confirm_text
        data["context_based_assistant"] = self._context_based_assistant

        async with self._sessionmaker() as session:
            repo = UserRepo(
                user_gateway=UserGateWay(session=session)
            )
            data["user_repo"] = repo

            await handler(event, data)
