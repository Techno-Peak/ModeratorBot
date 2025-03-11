from aiogram import Router, types
from aiogram.filters import Command

link_router = Router()


@link_router.message(Command('remove'))
async def remove_links(message: types.Message):
    await message.answer(
        "Link remove"
    )
