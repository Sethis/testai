
from io import BytesIO
from abc import ABC, abstractmethod

from openai import AsyncClient

from testai.src.interactors.processing.getname import GetUniqueNameProtocol


class TextToAudioInteractor(ABC):
    @abstractmethod
    async def get_response(self, text: str, getname: GetUniqueNameProtocol) -> BytesIO:
        raise NotImplementedError()


class TTSTextToAudio(TextToAudioInteractor):
    __slots__ = ("_client",)

    def __init__(self, client: AsyncClient):
        self._client = client

    async def get_response(self, text: str, getname: GetUniqueNameProtocol) -> BytesIO:
        io = BytesIO()
        io.name = getname(".mp3")

        async with self._client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="alloy",
                input=text,
        ) as response:
            io.write(await response.read())

        io.seek(0)

        return io
