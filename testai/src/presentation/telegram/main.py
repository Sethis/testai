

import asyncio

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import SimpleEventIsolation, MemoryStorage
from openai import AsyncClient

from testai.config.config_reader import get_config
from testai.src.presentation.telegram.routers import audio
from testai.src.presentation.telegram.middlewares.di import DIMiddleware


async def main():
    config = get_config()

    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=MemoryStorage(), events_isolation=SimpleEventIsolation())

    openai = AsyncClient(api_key=config.openai_key)

    dp.message.middleware(DIMiddleware(client=openai))
    dp.callback_query.middleware(DIMiddleware(client=openai))

    dp.include_router(audio.router)

    await dp.start_polling(bot)


asyncio.run(main())
