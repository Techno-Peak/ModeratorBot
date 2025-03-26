import asyncio
import re
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatMember
from aiogram.enums import ChatMemberStatus
from database.models import User, Group, BlockedWord, Invite
from config import bot
from handlers.utils import delete_after_delay, AUTO_DELETE_TIME_INTERVAL, delete_message


user_router = Router()


# Umumiy xabarlarni boshqarish
@user_router.message()
async def handle_message_user(message: Message):
    if message.chat.type in ['group', 'supergroup']:
        chat = message.chat
        tg_user = message.from_user
        user = await User.get_or_create(
            chat_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name
        )

        _group = await Group.get_or_create(message.chat.id, message.chat.title)

        if not _group.is_activate:
            bot_member = await message.bot.get_chat_member(chat.id, message.bot.id)

            if bot_member.status in [ChatMemberStatus.ADMINISTRATOR]:
                await _group.activate()
                sm = await message.bot.send_message(
                    chat_id=message.chat.id,
                    text=(
                        "✅ <b>Guruh muvaffaqiyatli faollashtirildi!</b>\n\n"
                        f"🏷 <b>Guruh nomi:</b> <a href='tg://user?id={_group.chat_id}'>#{_group.title}</a>\n"
                        "📢 Endi guruh a'zolari bot xizmatlaridan to‘liq foydalanishlari mumkin.\n"
                    ),
                    parse_mode="HTML"
                )
                asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))


        if message.left_chat_member:
            await delete_message(message)
            return

        if message.new_chat_members:
            invite = await Invite.get_invite(
                group_chat_id=message.chat.id,
                user_chat_id=message.from_user.id
            )
            for new_member in message.new_chat_members:
                invite = await invite.add_invite(invited_chat_id=new_member.id)
            await delete_message(message)
            return

        if message.left_chat_member or message.new_chat_members:
            await delete_message(message)

        chat_admins = await message.bot.get_chat_administrators(message.chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]
        _user = await User.get_user(message.from_user.id)

        if tg_user.id in admin_ids:
            return

        if message.story:
            await delete_message(message)
            return
        
        if _group and _group.required_channel and await is_user_subscribed(_group.required_channel, tg_user.id):
            if tg_user.first_name == 'Channel':
                try:
                    await delete_message(message)
                except Exception as e:
                    print(f"Kanal xabarini o‘chirishda xatolik: {e}")
                return

        if user:
            if message.forward_date:
                try:
                    await delete_message(message)
                    print(f"Forward qilingan linkli xabar o‘chirildi:")
                except Exception as e:
                    print(f"Forward xabarni o‘chirishda xatolik: {e}")

            elif message.text and has_link(message.html_text):
                try:
                    await delete_message(message)
                    sm = await message.bot.send_message(
                        chat_id=message.chat.id,
                        text=f"❗️<b>Diqqat, <a href=\"tg://user?id={message.from_user.id}\">{message.from_user.full_name}</a></b>! "
                             f"reklama tarqatmang!",
                        parse_mode="HTML"
                    )
                    asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))
                    print(f"Link yoki username o‘chirildi.")
                except Exception as e:
                    print(f"Xabarni o‘chirishda xatolik: {e}")
        else:
            try:
                chat = await bot.get_chat(_group.required_channel)
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

                sm = await message.bot.send_message(
                    chat_id=message.chat.id,
                    text=(
                        f"📢 <b>Diqqat, <a href=\"tg://user?id={message.from_user.id}\">{message.from_user.full_name}</a>!</b>\n\n"
                        "Guruhdan to‘liq foydalanish uchun avval quyidagi kanalga a'zo bo‘lishingiz kerak.👇"
                    ),
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=keyboard
                )

                await delete_message(message)
                asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))

        invite = await Invite.get_invite(
            group_chat_id=message.chat.id,
            user_chat_id=message.from_user.id
        )

        if invite and invite.count < _group.required_members:

            remaining = _group.required_members - invite.count
            user_mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a>"

            sm = await message.bot.send_message(
                chat_id=message.chat.id,
                text=f"❗ {user_mention}, siz hali guruhga kerakli odam sonini qo‘shmagansiz.\n\n"
                f"📢 Yana {remaining} ta odam taklif qilishingiz kerak.\n\n"
                f"/meni - Men qo'shgan odamlar soni!",
                parse_mode="HTML"
            )
            await delete_message(message)
            asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))
            return

        if await is_blocked_message(message.text):
            await delete_message(message)
            return


@user_router.edited_message()
async def edited_message(message: Message):
    if message.chat.type in ['group', 'supergroup']:
        tg_user = message.from_user
        user = await User.get_or_create(
            chat_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name
        )

        _group = await Group.get_or_create(message.chat.id, message.chat.title)
        if not _group.is_activate:
            return

        chat_admins = await message.bot.get_chat_administrators(message.chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]
        _user = await User.get_user(message.from_user.id)

        if tg_user.id in admin_ids:
            return

        if message.story:
            await delete_message(message)
            return

        if _group and _group.required_channel and await is_user_subscribed(_group.required_channel, tg_user.id):
            if tg_user.first_name == 'Channel':
                try:
                    await delete_message(message)
                except Exception as e:
                    print(f"Kanal xabarini o‘chirishda xatolik: {e}")
                return

        if user:
            if message.forward_date:
                try:
                    await delete_message(message)
                    print(f"Forward qilingan linkli xabar o‘chirildi:")
                except Exception as e:
                    print(f"Forward xabarni o‘chirishda xatolik: {e}")

            elif message.text and has_link(message.html_text):
                try:
                    await delete_message(message)
                    sm = await message.bot.send_message(
                        chat_id=message.chat.id,
                        text=f"❗️<b>Diqqat, <a href=\"tg://user?id={message.from_user.id}\">{message.from_user.full_name}</a></b>"
                             f"! reklama tarqatmang!",
                        parse_mode="HTML"
                    )
                    asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))
                    print(f"Link yoki username o‘chirildi.")
                except Exception as e:
                    print(f"Xabarni o‘chirishda xatolik: {e}")
        else:
            try:
                chat = await bot.get_chat(_group.required_channel)
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

                sm = await message.bot.send_message(
                    chat_id=message.chat.id,
                    text=(
                        f"📢 <b>Diqqat, <a href=\"tg://user?id={message.from_user.id}\">{message.from_user.full_name}</a>!</b>\n\n"
                        "Guruhdan to‘liq foydalanish uchun avval quyidagi kanalga a'zo bo‘lishingiz kerak.👇"
                    ),
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=keyboard
                )

                await delete_message(message)
                asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))

        if await is_blocked_message(message.text):
            await delete_message(message)
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
