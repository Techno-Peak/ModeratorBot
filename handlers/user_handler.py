import asyncio
import re
from aiogram import Router
from aiogram.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, ChatMember, ContentType
from aiogram.enums import ChatMemberStatus
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from database.models import User, Group, BlockedWord
from config import bot
from handlers.utils import delete_after_delay, AUTO_DELETE_TIME_INTERVAL


user_router = Router()


# Umumiy xabarlarni boshqarish
@user_router.message()
async def handle_message_user(message: Message):
    if message.chat.type in ['group', 'supergroup'] and await Group._is_activate(message.chat.id):
        if message.left_chat_member or message.new_chat_members:
            await message.delete()
            return

        tg_user = message.from_user

        if message.left_chat_member or message.new_chat_members:
            await message.delete()

        chat_admins = await message.bot.get_chat_administrators(message.chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]
        group = await Group.get_group(message.chat.id)

        if tg_user.id in admin_ids:
            return
        
        if group and group.required_channel and await is_user_subscribed(group.required_channel, tg_user.id):
            if tg_user.first_name == 'Channel':
                try:
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
                        await message.delete()
                        print(f"Forward qilingan linkli xabar o‘chirildi:")
                    except Exception as e:
                        print(f"Forward xabarni o‘chirishda xatolik: {e}")

                elif message.text and has_link(message.text):
                    try:
                        await message.delete()
                        print(f"Link yoki username o‘chirildi.")
                    except Exception as e:
                        print(f"Xabarni o‘chirishda xatolik: {e}")
        else:
            try:
                chat = await bot.get_chat(group.required_channel)
                if chat.username: 
                    channel_url = f"https://t.me/{chat.username}"
                else:
                    channel_url = None
            except Exception as e:
                channel_url = None 

            if channel_url:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="📢 Obuna bo‘lish", url=channel_url)]
                    ]
                )

                sm = await message.reply(
                    f"📢 Guruhdan foydalanish uchun avval quyidagi kanalga a'zo bo‘lishingiz kerak:",
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=keyboard
                )
                await message.delete()
                asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))

        if await is_blocked_message(message.text):
            await message.delete()
            return
        
        
# Linklarni tekshirish
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


# Yangi foydalanuvchi qo'shilsa xabar yuborish
@user_router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    if await Group._is_activate(event.chat.id):
        group = await Group.get_or_create(event.chat.id, event.chat.title)
        user = event.from_user
        required_channel = group.required_channel

        if required_channel and not await is_user_subscribed(required_channel, user.id):
            try:
                chat = await bot.get_chat(required_channel)
                if chat.username: 
                    channel_url = f"https://t.me/{chat.username}"
                else:
                    channel_url = None
            except Exception as e:
                channel_url = None 

            if channel_url:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="📢 Obuna bo‘lish", url=channel_url)]
                    ]
                )

                sm = await event.answer(
                    f"Assalomu alaykum, <a href=\"tg://user?id={user.id}\">{user.full_name}</a>! {event.chat.title} guruhiga xush kelibsiz.\n\n"
                    f"📢 Guruhdan foydalanish uchun avval quyidagi kanalga a'zo bo‘lishingiz kerak:",
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=keyboard
                )
            else:
               sm = await event.answer(
                    "⚠️ Kechirasiz, kanalga obuna bo‘lish havolasini olish imkonsiz. Iltimos, admin bilan bog‘laning!"
                )
        else:
            sm = await event.answer(
                f"Assalomu alaykum! Siz {event.chat.title} guruhiga qo‘shildingiz."
            )

        if sm:
            asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))

# Bot kanaliga azoligini tekshirish
async def is_user_subscribed(channel_id: int, user_id: int) -> bool:
    try:
        member: ChatMember = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        return False


async def contains_blocked_word(text: str, words_subset: list) -> bool:
    words = text.lower().split()
    return any(word in words_subset for word in words)

async def is_blocked_message(text: str) -> bool:
    blocked_words = await BlockedWord.get_blocked_words()
    if not blocked_words:
        return False
    
    num_tasks = max(len(blocked_words) // 5, 1)
    word_chunks = [
        blocked_words[i:i + (len(blocked_words) // num_tasks)]
        for i in range(0, len(blocked_words), len(blocked_words) // num_tasks)
    ]

    tasks = [contains_blocked_word(text.lower(), chunk) for chunk in word_chunks]
    results = await asyncio.gather(*tasks)
    return any(results)
