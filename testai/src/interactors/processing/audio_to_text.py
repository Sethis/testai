

from io import BytesIO
from typing import BinaryIO
from abc import ABC, abstractmethod

from openai import AsyncClient

from testai.src.interactors.processing.getname import GetUniqueNameProtocol


class AudioToTextInteractor(ABC):
    @abstractmethod
    async def get_response(
            self,
            audio: BinaryIO,
            getname: GetUniqueNameProtocol
    ) -> str:
        raise NotImplementedError()


class WhisperAudioToTextInteractor(AudioToTextInteractor):
    __slots__ = ("_client",)

    def __init__(self, client: AsyncClient):
        self._client = client

    async def get_response(
            self,
            audio: BinaryIO,
            getname: GetUniqueNameProtocol
    ) -> str:

        io = BytesIO()
        io.name = getname(".mp3")

        io.write(audio.read())
        io.seek(0)

        translation = await self._client.audio.translations.create(
            model="whisper-1",
            file=io
        )

        return translation.text
