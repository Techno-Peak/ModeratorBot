from aiogram import Router, types
from aiogram.filters import Command

blocked_words_router = Router()


@blocked_words_router.message(Command('block'))
async def check_blocked_words(message: types.Message):
    await message.answer(
        "Blocked word"
    )