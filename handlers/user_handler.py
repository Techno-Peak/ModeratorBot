from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from database.models import User

user_router = Router()


@user_router.message()
async def register_user(message: Message):
    if message.chat.type in ['group', 'supergroup']:
        user = message.from_user

        new_user = await User.get_or_create(
            chat_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        print(f"{user.first_name} (ID: {user.id}) bazaga qo‘shildi yoki topildi!")


