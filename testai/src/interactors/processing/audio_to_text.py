

from io import BytesIO

from typing import BinaryIO
from abc import ABC, abstractmethod

from openai import AsyncClient


class AudioToTextInteractor(ABC):
    @abstractmethod
    async def get_response(self, audio: BinaryIO) -> str:
        raise NotImplementedError()


class WhisperAudioToTextInteractor(AudioToTextInteractor):
    __slots__ = ("_client",)

    def __init__(self, client: AsyncClient):
        self._client = client

    async def get_response(self, audio: BinaryIO) -> str:
        io = BytesIO()
        io.name = "response.mp3"

        io.write(audio.read())
        io.seek(0)

        translation = await self._client.audio.translations.create(
            model="whisper-1",
            file=io
        )

        return translation.text
