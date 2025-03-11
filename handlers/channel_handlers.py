from aiogram import Router, types
from aiogram.filters import Command

channel_router = Router()
CHANNEL_ID = -100123456789  # Kanal ID sini yozing

@channel_router.message(Command("start"))
async def check_channel_subscription(message: types.Message):
    await message.answer(
        "Channel handlers"
    )