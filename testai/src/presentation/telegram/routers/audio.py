

import json
from io import BytesIO
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from testai.src.interactors.database.repositories.user import User, UserRepo
from testai.src.interactors.processing.text_to_response import (
    TextToResponseInteractor,
    ContextBasedInteractor,
    ContextBasedResponseContainer,
    ConfirmTextFormat
)
from testai.src.interactors.processing.audio_to_text import AudioToTextInteractor
from testai.src.interactors.processing.text_to_audio import TextToAudioInteractor
from testai.src.interactors.processing.getname import SimpleGetUniqueName

router = Router()


class AudioState(StatesGroup):
    write_assis_name = State()
    write_audio = State()
    write_mental = State()


class AssistantChoice(CallbackData, prefix="choice_assistants"):
    id: str


def render_user_menu(user: User) -> [str, InlineKeyboardMarkup]:
    text = "Please, choice your assistant: "

    builder = InlineKeyboardBuilder()

    assistants = user.assistants or []

    for assistant in assistants:
        builder.add(
            InlineKeyboardButton(
                text=assistant.name,
                callback_data=AssistantChoice(id=assistant.openai_id).pack()
            )
        )

    builder.add(
        InlineKeyboardButton(
            text="+ Add",
            callback_data="add_new_assistants"
        )
    )

    builder.adjust(3)

    return text, builder.as_markup()


@router.message(Command(commands=["start"]))
async def on_start(message: Message, user_repo: UserRepo, state: FSMContext):
    await state.clear()

    user = await user_repo.get_user_by_tg_id_unsafe(message.from_user.id)

    if not user:
        user = await user_repo.upsert_user(message.from_user.id)

    render = render_user_menu(user)

    await message.answer(text=render[0], reply_markup=render[1])


@router.message(Command(commands=["profile"]))
async def on_start(message: Message, user_repo: UserRepo, state: FSMContext):
    await state.clear()

    user = await user_repo.get_user_by_tg_id_unsafe(message.from_user.id)

    if not user:
        await message.answer("Text the /start first")
        return

    await message.answer(
        f"Hello!\n"
        f"Your id: <b>{user.id}</b>\n"
        f"Your tg id: <b>{user.tg_id}</b>\n"
        f"Your profession: <b>{user.mental.profession or 'use /mental'}</b>\n"
        f"Your temperament: <b>{user.mental.temperament or 'use /mental'}</b>\n"
    )


@router.message(Command(commands=["mental"]))
async def on_start(
        message: Message,
        bot: Bot,
        user_repo: UserRepo,
        context_based_assistant: ContextBasedInteractor,
        text_to_audio: TextToAudioInteractor,
        audio_to_text: AudioToTextInteractor,
        state: FSMContext
):
    await state.clear()

    user = await user_repo.get_user_by_tg_id(message.from_user.id)

    if not user:
        await message.answer("Text the /start first")
        return

    new_thread = await context_based_assistant.new_thread()
    assistant = await context_based_assistant.new_assistant()

    await state.update_data(
        thread_id=new_thread,
        assistant_id=assistant
    )
    await state.set_state(AudioState.write_mental)

    input_file, audio, context = await get_mental_audio_response(
        bot=bot,
        user_id=user.id,
        thread_id=new_thread,
        assistant_id=assistant,
        context_based_assistant=context_based_assistant,
        text_to_audio=text_to_audio,
        audio_to_text=audio_to_text,
        text="Hello!"
    )

    await message.answer_voice(
        input_file,
        caption="You can continue the conversation by sending another voice or text message"
    )

    del input_file, audio


@router.callback_query(F.data == "add_new_assistants")
async def on_new_assistant_click(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Write me a name of your future assistant: ")

    await state.set_state(AudioState.write_assis_name)


@router.message(AudioState.write_assis_name)
async def on_start(message: Message, user_repo: UserRepo, text_to_response: TextToResponseInteractor):
    assistant_id = await text_to_response.new_assistant(
        name=message.text,
        instructions="Be friendly and positive"
    )

    user = await user_repo.get_user_by_tg_id(message.from_user.id)
    await user_repo.add_assistant(user_id=user.id, openai_id=assistant_id, name=message.text)
    user = await user_repo.get_user_by_id(user_id=user.id)

    render = render_user_menu(user)

    await message.answer(text=render[0], reply_markup=render[1])


@router.callback_query(AssistantChoice.filter())
async def on_new_assistant_click(
        callback: CallbackQuery,
        state: FSMContext,
        callback_data: AssistantChoice
):

    await state.update_data(assistant_id=callback_data.id)
    await state.set_state(AudioState.write_audio)

    await callback.message.edit_text("Send me your voice message with your cool request:")


async def get_audio_response(
        bot: Bot,
        text_to_response: TextToResponseInteractor,
        audio_to_text: AudioToTextInteractor,
        text_to_audio: TextToAudioInteractor,
        voice_file_id: str,
        user_id: int,
        assistant_id: str,
        thread_id: str
) -> tuple[BufferedInputFile, BytesIO]:
    audio = await bot.download(voice_file_id)
    if not audio:
        raise ValueError("Audio undefined")

    getname = SimpleGetUniqueName(user_id=user_id)

    text = await audio_to_text.get_response(audio, getname=getname)
    del audio

    response = await text_to_response.get_response(
        request=text,
        assistant_id=assistant_id,
        thread_id=thread_id
    )

    # getname context based so getname() != getname()
    new_audio = await text_to_audio.get_response(response, getname=getname)

    return BufferedInputFile(file=new_audio.read(), filename=getname(".mp3")), new_audio


@router.message(AudioState.write_audio)
async def on_start(
        message: Message,
        bot: Bot,
        text_to_response: TextToResponseInteractor,
        audio_to_text: AudioToTextInteractor,
        text_to_audio: TextToAudioInteractor,
        state: FSMContext
):

    if not message.voice:
        await message.answer("It's not a voice message")
        return

    data = await state.get_data()

    assistant_id = data["assistant_id"]

    if data.get("thread_id", None):
        thread_id = data["thread_id"]

    else:
        thread_id = await text_to_response.new_thread()
        await state.update_data(thread_id=thread_id)

    input_file, audio = await get_audio_response(
        bot=bot,
        text_to_response=text_to_response,
        audio_to_text=audio_to_text,
        text_to_audio=text_to_audio,
        voice_file_id=message.voice.file_id,
        user_id=message.from_user.id,
        assistant_id=assistant_id,
        thread_id=thread_id
    )

    await message.answer_voice(
        input_file,
        caption="You can continue the conversation by sending another voice message"
    )

    del input_file, audio


async def get_mental_audio_response(
        bot: Bot,
        user_id: int,
        thread_id: str,
        assistant_id: str,
        context_based_assistant: ContextBasedInteractor,
        text_to_audio: TextToAudioInteractor,
        audio_to_text: AudioToTextInteractor,
        text: Optional[str] = None,
        voice_file_id: Optional[str] = None
) -> tuple[Optional[BufferedInputFile], Optional[BytesIO], ContextBasedResponseContainer]:
    if voice_file_id:
        audio = await bot.download(voice_file_id)
        if not audio:
            raise ValueError("Audio undefined")

        getname = SimpleGetUniqueName(user_id=user_id)

        text = await audio_to_text.get_response(audio, getname=getname)

    if not text:
        raise ValueError("Undefined text")

    response = await context_based_assistant.get_response(
        request=text,
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    if not response.text.strip():
        return None, None, response

    getname = SimpleGetUniqueName(user_id=user_id)

    # getname context based so getname() != getname()
    new_audio = await text_to_audio.get_response(response.text, getname=getname)

    return BufferedInputFile(file=new_audio.read(), filename=getname(".mp3")), new_audio, response


@router.message(AudioState.write_mental)
async def on_start(
        message: Message,
        bot: Bot,
        user_repo: UserRepo,
        context_based_assistant: ContextBasedInteractor,
        text_to_audio: TextToAudioInteractor,
        audio_to_text: AudioToTextInteractor,
        confirm_text: ConfirmTextFormat,
        state: FSMContext
):

    if not message.voice and not message.text:
        await message.answer("It's not a voice message or text message")
        return

    voice_file_id = None
    if message.voice:
        voice_file_id = message.voice.file_id

    data = await state.get_data()

    assistant_id = data["assistant_id"]
    thread_id = data["thread_id"]

    user = await user_repo.get_user_by_tg_id(message.from_user.id)

    input_file, audio, context = await get_mental_audio_response(
        bot=bot,
        user_id=user.id,
        thread_id=thread_id,
        assistant_id=assistant_id,
        context_based_assistant=context_based_assistant,
        text_to_audio=text_to_audio,
        audio_to_text=audio_to_text,
        text=message.text,
        voice_file_id=voice_file_id
    )

    if context.text:
        caption = context.text or None

        await message.answer_voice(
            input_file,
            caption=caption
        )

    if context.context:
        confirm_result = await confirm_text.confirm(
            system_text=(
                "You only have to answer whether the user's messages match the format: "
                "profession: string, temperament: string "
                "and does not contain humorous or strange formulas"
            ),
            text=context.context
        )

        if confirm_result:
            result_data = json.loads(context.context)
            await user_repo.upsert_user_mental(
                user_id=user.id,
                temperament=result_data["temperament"],
                profession=result_data["profession"]
            )
            await message.answer("Sucess! Check your result in /profile")

        else:
            await message.answer("The mental test failed! Try it again /mental")

        await state.clear()

    del input_file, audio
