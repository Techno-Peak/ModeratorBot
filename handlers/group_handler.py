from aiogram import Router, types
from aiogram.filters import Command

group_router = Router()

@group_router.message(Command("start"))
async def check_channel_subscription(message: types.Message):
    await message.answer(
        "Channel handlers"
    )