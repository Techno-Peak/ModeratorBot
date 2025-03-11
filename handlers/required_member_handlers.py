from aiogram import Router, types
from aiogram.filters import Command

required_members_router = Router()


@required_members_router.message(Command('add'))
async def check_required_members(message: types.Message):
    await message.answer(
        "Required members"
    )
