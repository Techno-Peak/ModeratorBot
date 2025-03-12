from aiogram import Router
from aiogram.types import Message
from database.models import User, Group
import re

user_router = Router()

@user_router.message()
async def handle_message_user(message: Message):
    if message.chat.type in ['group', 'supergroup'] and await Group._is_activate(message.chat.id):
        tg_user = message.from_user

        if tg_user.first_name == 'Channel':
            try:
                await message.reply(f"Bu guruhda kanal nomidan yozish taqiqlanadi!!")
                await message.delete()
            except Exception as e:
                print(f"Kanal xabarini o‘chirishda xatolik: {e}")
            return

        user = await User.get_or_create(
                chat_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name
            )

        if user:
            if message.forward_date:
                try:
                    await message.reply(f"{user.first_name}, forward qilish mumkin emas.")
                    await message.delete()
                    print(f"Forward qilingan linkli xabar o‘chirildi:")
                except Exception as e:
                    print(f"Forward xabarni o‘chirishda xatolik: {e}")

            elif message.text and has_link(message.text):
                try:
                    await message.reply(f"{user.first_name}, bu guruhda link yuborish mumkin emas!!")
                    await message.delete()
                    print(f"Link yoki username o‘chirildi.")
                except Exception as e:
                    print(f"Xabarni o‘chirishda xatolik: {e}")
            
        

def has_link(text: str) -> bool:
    link_pattern = r"""
        (?:
            (?:https?://|www\.)             
            |                                
            [a-zA-Z0-9-]+\.[a-zA-Z]{2,}       
            |                                 
            @[\w\d_]+                          
        )
        [^\s]*                                
    """
    return bool(re.search(link_pattern, text, re.VERBOSE | re.IGNORECASE))


