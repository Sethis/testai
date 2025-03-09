

import asyncio

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import SimpleEventIsolation, MemoryStorage
from openai import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from testai.config.config_reader import get_config
from testai.src.presentation.telegram.routers import audio
from testai.src.presentation.telegram.middlewares.di import DIMiddleware


async def main():
    config = get_config()

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage(), events_isolation=SimpleEventIsolation())

    openai = AsyncClient(api_key=config.openai_key)

    engine = create_async_engine(
        config.get_sqlalchemy_database_url(),
        pool_size=50,
        pool_timeout=15,
        pool_recycle=1500,
        pool_pre_ping=True,
        max_overflow=30,
        connect_args={
            "server_settings": {"jit": "off"}
        }
    )

    sessionmaker = async_sessionmaker(engine, autoflush=False, expire_on_commit=False)

    dp.message.middleware(DIMiddleware(client=openai, sessionmaker=sessionmaker))
    dp.callback_query.middleware(DIMiddleware(client=openai, sessionmaker=sessionmaker))

    dp.include_router(audio.router)

    await dp.start_polling(bot)


asyncio.run(main())
