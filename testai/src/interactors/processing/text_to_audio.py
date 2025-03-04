
from io import BytesIO
from abc import ABC, abstractmethod

from openai import AsyncClient


class TextToAudioInteractor(ABC):
    @abstractmethod
    async def get_response(self, text: str) -> BytesIO:
        raise NotImplementedError()


class TTSTextToAudio(TextToAudioInteractor):
    __slots__ = ("_client",)

    def __init__(self, client: AsyncClient):
        self._client = client

    async def get_response(self, text: str) -> BytesIO:
        io = BytesIO()

        async with self._client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="alloy",
                input=text,
        ) as response:
            io.write(await response.read())

        io.seek(0)

        return io
