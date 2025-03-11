from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

admin_router = Router()

@admin_router.message(Command('link'))
async def remove_join_leave_messages(message: Message):
    await message.answer(
        "Joined message word"
    )

