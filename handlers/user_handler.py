from aiogram import Router, types
from aiogram.filters import Command

user_router = Router()


@user_router.message(Command('block'))
async def check_blocked_words(message: types.Message):
    await message.answer(
        "Blocked word"
    )