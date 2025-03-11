from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

joined_router = Router()

@joined_router.message(Command('link'))
async def remove_join_leave_messages(message: Message):
    await message.answer(
        "Joined message word"
    )

