

from aiogram import Router, F, Bot
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from testai.src.interactors.database.repositories.user import User, UserRepo
from testai.src.interactors.processing.text_to_response import TextToResponseInteractor
from testai.src.interactors.processing.audio_to_text import AudioToTextInteractor
from testai.src.interactors.processing.text_to_audio import TextToAudioInteractor

router = Router()


class AudioState(StatesGroup):
    write_assis_name = State()
    write_audio = State()


class AssistantChoice(CallbackData, prefix="choice_assistants"):
    id: str


def render_user_menu(user: User) -> [str, InlineKeyboardMarkup]:
    text = "Please, choice your assistant: "

    builder = InlineKeyboardBuilder()

    for assistant in user.assistants:
        builder.add(
            InlineKeyboardButton(
                text=assistant.name,
                callback_data=AssistantChoice(id=assistant.id).pack()
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
async def on_start(message: Message, user_repo: UserRepo):
    user = await user_repo.get_user_by_tg_id(message.from_user.id)

    render = render_user_menu(user)

    await message.answer(text=render[0], reply_markup=render[1])


@router.callback_query(F.data == "add_new_assistants")
async def on_new_assistant_click(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Write me the name of your future assistant: ")

    await state.set_state(AudioState.write_assis_name)


@router.message(AudioState.write_assis_name)
async def on_start(message: Message, user_repo: UserRepo, text_to_response: TextToResponseInteractor):
    assistant_id = await text_to_response.new_assistant(
        name=message.text,
        instructions="Be friendly and positive"
    )

    user = await user_repo.get_user_by_tg_id(message.from_user.id)
    await user_repo.add_assistant(user_id=user.id, assistant_id=assistant_id, name=message.text)
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

    if data.get("thread", None):
       thread_id = data["thread_id"]

    else:
        thread_id = await text_to_response.new_thread()
        await state.update_data(thread_id=thread_id)

    audio = await bot.download(message.voice.file_id)
    if not audio:
        raise ValueError("Audio undefined")

    text = await audio_to_text.get_response(audio)

    response = await text_to_response.get_response(
        request=text,
        assistant_id=assistant_id,
        thread_id=thread_id
    )

    new_audio = await text_to_audio.get_response(response)
    input_file = BufferedInputFile(file=new_audio.read(), filename="")

    await message.answer_voice(
        input_file,
        caption="You can continue the conversation by sending another voice message"
    )
