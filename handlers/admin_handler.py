import asyncio

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.models import BlockedWord, User, Group
from handlers.utils import delete_after_delay, AUTO_DELETE_TIME_INTERVAL, delete_message

admin_router = Router()

@admin_router.message(Command('word'))
async def add_blocked_word(message: Message):
    if message.chat.type == 'private':
        from_user = message.from_user

        user = await User.get_user(chat_id=from_user.id)

        if not (user and user.is_admin):
            await message.reply(
                text="⚠️ Ushbu buyruqdan faqat <b>adminlar</b> foydalanishi mumkin!\n\n",
                parse_mode="HTML"
            )
            return

        command_args = message.text.split(maxsplit=1)
        if len(command_args) < 2:
            await message.reply(
                text="ℹ️ Iltimos, buyruq bilan birga so‘zni ham yuboring.\n\n"
                     "📌 Misol: <code>/word yomon_so'z</code>",
                parse_mode="HTML"
            )
            return

        new_word = command_args[1].strip().lower()

        # So‘z bazada bor yoki yo‘qligini tekshiramiz
        blocked_words = await BlockedWord.get_blocked_words()
        if new_word in blocked_words:
            sm = await message.reply(
                text=f"⚠️ <b>{new_word[0]}...{new_word[-1]}</b> so‘zi allaqachon bloklangan!",
                parse_mode="HTML"
            )
        else:
            # Yangi so‘zni bazaga qo‘shamiz
            await BlockedWord.create(new_word)
            sm = await message.reply(
                text=f"✅ <b>{new_word[0]}...{new_word[-1]}</b> so‘zi bloklangan so‘zlar ro‘yxatiga qo‘shildi!",
                parse_mode="HTML"
            )

    else:
        sm = await message.bot.send_message(
            chat_id=message.chat.id,
            text="ℹ️ <b>/word</b> buyrug‘idan faqat bot bilan shaxsiy chatda foydalanish mumkin.\n\n"
                 "Iltimos, ushbu buyruqni botga shaxsiy xabarda yuboring.",
            parse_mode="HTML"
        )
        asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))
        await delete_message(message)


@admin_router.message(Command('count'))
async def required_members(message: Message):
    if message.chat.type in ['group', 'supergroup']:
        user = message.from_user
        _group = await Group.get_or_create(message.chat.id, message.chat.title)

        if not _group.is_activate:
            sm = await message.bot.send_message(
                chat_id=message.chat.id,
                text="❌ Bot hali ushbu guruhga ulanmagan.\n\n"
                     "🔗 Botni faollashtirish uchun quyidagi buyruqni yuboring:\n"
                     "<code>/activate</code>",
                parse_mode="HTML"
            )
            await delete_message(message)
            asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))
            return

        chat_admins = await message.bot.get_chat_administrators(message.chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]

        if user.id not in admin_ids:
            sm = await message.bot.send_message(
                chat_id=message.chat.id,
                text=f"⚠️ Hurmatli <a href=\"tg://user?id={user.id}\">{user.full_name}</a>, siz ushbu buyruqdan foydalanish huquqiga ega emassiz!\n\n"
                     "📌 Faqat guruh administratorlari <b>/count</b> buyrug‘idan foydalanishi mumkin.",
                parse_mode="HTML"
            )
            asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))
            await delete_message(message)
            return

        command_args = message.text.split(maxsplit=1)
        if len(command_args) < 2:
            sm = await message.bot.send_message(
                chat_id=message.chat.id,
                text="ℹ️ Iltimos, buyruq bilan birga majburiy qo'shilishi kerak bo'lgan odamlar sonini ham yuboring.\n\n"
                     "📌 Misol: <code>/count 5</code>",
                parse_mode="HTML"
            )
            asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))
            await delete_message(message)
            return

        _count = command_args[1]
        if _count.isdigit():
            required_count = int(_count)
            await _group.updated_required_members(count=required_count)
            if required_count > 0:
                sm = await message.bot.send_message(
                    chat_id=message.chat.id,
                    text=f"✅ Guruhga majburiy qo‘shilishi kerak bo‘lgan odamlar soni <b>{required_count}</b> ga o‘rnatildi.\n\n"
                         "📌 Endi guruhda yozish uchun foydalanuvchilar ushbu limitga javob berishi kerak.\n\n"
                         "✏️ Agar bu sonni o‘zgartirmoqchi bo‘lsangiz, quyidagi formatda yangi sonni kiriting:\n"
                         "<code>/count [yangi son]</code>\n\n"
                         "❌ Agar bu talabni o‘chirmoqchi bo‘lsangiz, quyidagi buyruqni yuboring:\n"
                         "<code>/count 0</code>",
                    parse_mode="HTML"
                )
            else:
                sm = await message.bot.send_message(
                    chat_id=message.chat.id,
                    text="✅ Guruhga majburiy qo‘shilish talabi bekor qilindi.\n\n"
                         "📌 Endi foydalanuvchilar cheklovsiz yozishlari mumkin.\n\n"
                         "✏️ Agar bu talabni qayta yoqmoqchi bo‘lsangiz, yangi limitni quyidagi formatda kiriting:\n"
                         "<code>/count [yangi son]</code>",
                    parse_mode="HTML"
                )
        else:
            sm = await message.bot.send_message(
                chat_id=message.chat.id,
                text="❌ Noto‘g‘ri format! Iltimos, faqat raqam kiriting.\n\n"
                     "✅ To‘g‘ri foydalanish namunasi:\n"
                     "<code>/count 5</code>",
                parse_mode="HTML"
            )
        asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))
        await delete_message(message)

    else:
        sm = await message.bot.send_message(
            chat_id=message.chat.id,
            text="ℹ️ <b>/count</b> buyrug‘idan faqat guruhlarda foydalanish mumkin.\n\n"
                 "Iltimos, botni guruhga qo‘shing va ushbu buyruqdan foydalaning.",
            parse_mode="HTML"
        )
        asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))
        await delete_message(message)

@admin_router.message(Command('add_admin'))
async def add_admin(message: Message):
    if message.chat.type == 'private':
        from_user = message.from_user

        user = await User.get_user(chat_id=from_user.id)

        if not (user and user.is_admin):
            await message.reply(
                text="⚠️ Ushbu buyruqdan faqat <b>adminlar</b> foydalanishi mumkin!",
                parse_mode="HTML"
            )
            return

        command_args = message.text.split(maxsplit=1)
        if len(command_args) < 2:
            await message.reply(
                text="ℹ️ Iltimos, buyruq bilan birga foydalanuvchi ID kiriting.\n\n"
                     "📌 Misol: <code>/add_admin 123456789</code>",
                parse_mode="HTML"
            )
            return

        try:
            target_id = int(command_args[1].strip())
        except ValueError:
            await message.reply(
                text="⚠️ Noto‘g‘ri ID kiritildi. Iltimos, faqat raqam kiriting.",
                parse_mode="HTML"
            )
            return

        # Foydalanuvchini ID orqali topamiz
        target_user = await User.get_user(chat_id=target_id)

        if not target_user:
            await message.reply(
                text="⚠️ Foydalanuvchi bazada topilmadi!",
                parse_mode="HTML"
            )
            return

        target_full_name = (target_user.first_name + ' ') if target_user.first_name else ""
        target_full_name += target_user.last_name if target_user.last_name else ""
        if target_user.is_admin:
            await message.reply(
                text=f"ℹ️ <b><a href=\"tg://user?id={target_user.chat_id}\">{target_full_name}</a></b> allaqachon admin!",
                parse_mode="HTML"
            )
            return

        # Adminlikni yangilaymiz
        await target_user.update_is_admin(True)

        await message.reply(
            text=f"✅ <b><a href=\"tg://user?id={target_user.chat_id}\">{target_full_name}</a></b> endi admin sifatida belgilandi!",
            parse_mode="HTML"
        )

    else:
        sm = await message.bot.send_message(
            chat_id=message.chat.id,
            text="ℹ️ <b>/add_admin</b> buyrug‘idan faqat bot bilan shaxsiy chatda foydalanish mumkin.\n\n"
                 "Iltimos, ushbu buyruqni botga shaxsiy xabarda yuboring.",
            parse_mode="HTML"
        )
        asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))
        await delete_message(message)


@admin_router.message(Command('remove_admin'))
async def remove_admin(message: Message):
    if message.chat.type == 'private':
        from_user = message.from_user

        user = await User.get_user(chat_id=from_user.id)

        if not (user and user.is_admin):
            await message.reply(
                text="⚠️ Ushbu buyruqdan faqat <b>adminlar</b> foydalanishi mumkin!",
                parse_mode="HTML"
            )
            return

        command_args = message.text.split(maxsplit=1)
        if len(command_args) < 2:
            await message.reply(
                text="ℹ️ Iltimos, buyruq bilan birga foydalanuvchi ID kiriting.\n\n"
                     "📌 Misol: <code>/remove_admin 123456789</code>",
                parse_mode="HTML"
            )
            return

        try:
            target_id = int(command_args[1].strip())
        except ValueError:
            await message.reply(
                text="⚠️ Noto‘g‘ri ID kiritildi. Iltimos, faqat raqam kiriting.",
                parse_mode="HTML"
            )
            return

        # Foydalanuvchini ID orqali topamiz
        target_user = await User.get_user(chat_id=target_id)

        if not target_user or target_user.chat_id == 5547740249:
            await message.reply(
                text="⚠️ Foydalanuvchi bazada topilmadi!",
                parse_mode="HTML"
            )
            return

        target_full_name = (target_user.first_name + ' ') if target_user.first_name else ""
        target_full_name += target_user.last_name if target_user.last_name else ""

        if not target_user.is_admin:
            await message.reply(
                text=f"ℹ️ <b><a href=\"tg://user?id={target_user.chat_id}\">{target_full_name}</a></b> allaqachon admin emas!",
                parse_mode="HTML"
            )
            return

        # Adminlikni olib tashlaymiz
        await target_user.update_is_admin(False)

        await message.reply(
            text=f"✅ <b><a href=\"tg://user?id={target_user.chat_id}\">{target_full_name}</a></b> endi admin emas!",
            parse_mode="HTML"
        )

    else:
        sm = await message.bot.send_message(
            chat_id=message.chat.id,
            text="ℹ️ <b>/remove_admin</b> buyrug‘idan faqat bot bilan shaxsiy chatda foydalanish mumkin.\n\n"
                 "Iltimos, ushbu buyruqni botga shaxsiy xabarda yuboring.",
            parse_mode="HTML"
        )
        asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))
        await delete_message(message)
