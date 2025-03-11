import asyncio
import logging
from aiogram import Dispatcher
from config import dp, bot
from database.sessions import init_async_db
from handlers import *


async def on_startup(dispatcher: Dispatcher):
    print("Bot ishga tushdi!")
    await init_async_db()
    logging.info("Bot started successfully")


async def main():
    dp.include_router(admin_router)
    dp.include_router(group_router)
    dp.include_router(user_router)


    dp.startup.register(on_startup)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
