

from abc import ABC, abstractmethod

from openai import AsyncClient


class TextToResponseInteractor(ABC):
    @abstractmethod
    async def new_assistant(
            self,
            name: str,
            instructions: str
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def new_thread(
            self,
            name: str,
            instructions: str
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def get_response(
            self,
            request: str,
            instructions: str,
            thread_id: str,
            assistant_id: str
    ) -> str:
        raise NotImplementedError()


class AssistantTextToResponseInteractor(TextToResponseInteractor):
    __slots__ = ("_client", )

    def __init__(self, client: AsyncClient):
        self._client = client

    async def new_assistant(
            self,
            name: str,
            instructions: str
    ) -> str:
        assistant = await self._client.beta.assistants.create(
            name=name,
            instructions=instructions,
            model="gpt-4-1106-preview",
        )

        return assistant.id

    async def new_thread(
            self,
            name: str,
            instructions: str
    ) -> str:
        thread = await self._client.beta.threads.create()

        return thread.id

    async def get_response(
            self,
            request: str,
            instructions: str,
            thread_id: str,
            assistant_id: str
    ) -> str:
        stream = await self._client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            instructions=instructions,
            stream=True,
        )

        text = ""

        async for event in stream:
            try:
                text += event.data.delta.content[0].text.value

            except AttributeError:
                pass

        return text
