

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

from openai import AsyncClient
from openai.types.beta.assistant_stream_event import ThreadRunRequiresAction
from pydantic import BaseModel


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
            self
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def get_response(
            self,
            request: str,
            thread_id: str,
            assistant_id: str,
            instructions: Optional[str] = None,
    ) -> str:
        raise NotImplementedError()


class AssistantTextToResponseInteractor(TextToResponseInteractor):
    __slots__ = ("_client",)

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
            self
    ) -> str:
        thread = await self._client.beta.threads.create()

        return thread.id

    async def get_response(
            self,
            request: str,
            thread_id: str,
            assistant_id: str,
            instructions: Optional[str] = None
    ) -> str:
        await self._client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=request,
        )

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


@dataclass(slots=True, kw_only=True)
class ContextBasedResponseContainer:
    text: Optional[str] = None
    context: Optional[str] = None


class ContextBasedInteractor(ABC):
    @abstractmethod
    async def new_assistant(
            self,
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def new_thread(
            self,
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def get_response(
            self,
            request: str,
            thread_id: str,
            assistant_id: str
    ) -> ContextBasedResponseContainer:
        raise NotImplementedError()


class AssistantFunctionInteractor(ContextBasedResponseContainer):
    __slots__ = ("_client", "_cached")

    def __init__(self, client: AsyncClient):
        self._client = client
        self._cached = None

    async def get_response(
            self,
            request: str,
            thread_id: str,
            assistant_id: str
    ) -> ContextBasedResponseContainer:
        context = ContextBasedResponseContainer()

        await self._client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=request,
        )

        stream = await self._client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            stream=True,
        )

        text = ""

        async for event in stream:
            if isinstance(event, ThreadRunRequiresAction):
                context.context = (
                    event.data.required_action
                    .submit_tool_outputs.tool_calls[0]
                    .function.arguments
                )

                await self._client.beta.threads.runs.cancel(
                    thread_id=thread_id,
                    run_id=event.data.id
                )

            try:
                text += event.data.delta.content[0].text.value

            except AttributeError:
                pass

        context.text = text
        return context

    async def new_thread(self) -> str:
        thread = await self._client.beta.threads.create()

        return thread.id

    async def new_assistant(self) -> str:
        if self._cached:
            return self._cached

        assistant = await self._client.beta.assistants.create(
            instructions=(
                "You are a psychologist bot. "
                "Your task is ASK ONE QUESTION PER MESSAGE and THEN call the function. "
                "You don't have to ask questions directly. "
                "You can give several messages to one question for accuracy and "
                "in order to set up the user in a friendly way."
            ),
            model="gpt-4o",
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "save_value",
                        "description":
                            (
                                "This function determines the psychological representation of the user "
                                "with whom it communicates. It is called only after ALL the necessary answers "
                                "to the questions from the function parameters."
                            ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "profession": {
                                    "type": "string",
                                    "description": (
                                        "The user's job, or the job the user is studying for or planning to work for"
                                    )
                                },
                                "temperament": {
                                    "type": "string",
                                    "enum": ["Phlegmatic", "Sanguine", "Melancholic", "Choleric"],
                                    "description": (
                                        "The basis of a person's character, "
                                        "his standard reactions to others and situations"
                                    )
                                }
                            },
                            "required": ["profession", "temperament"],
                            "additionalProperties": False},
                        "strict": True
                    },
                },
            ]
        )

        self._cached = assistant.id

        return self._cached


class ConfirmTextFormat(ABC):
    @abstractmethod
    async def confirm(self, system_text: str, text: str) -> bool:
        raise NotImplementedError()


class Result(BaseModel):
    is_confirm_to_format: bool


class CompletitionsBasedConfirmTextFormat(ConfirmTextFormat):
    __slots__ = ("_client", )

    def __init__(self, client: AsyncClient):
        self._client = client

    async def confirm(self, system_text: str, text: str) -> bool:
        async with self._client.beta.chat.completions.stream(
                messages=[
                    {
                        "role": "system",
                        "content": system_text
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                model="gpt-4o-2024-08-06",
                response_format=Result
        ) as stream:
            last_result = None
            async for event in stream:
                if event.type == "content.delta":
                    if event.parsed is not None:
                        last_result = event.parsed

            if not last_result:
                raise ValueError("The message parsed with errors")

            return last_result["is_confirm_to_format"]
