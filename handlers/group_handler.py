import asyncio

from aiogram import Router, types
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import Group
from config import BOT_USERNAME, bot

group_router = Router()

NOT_ADMIN_TEXT = "🚫 Sizda ushbu buyruqni ishlatish uchun yetarli huquq yo‘q!\n\n" \
                "Bu buyruq faqat guruh administratorlari tomonidan bajarilishi mumkin."


# Xabarni kechikish bilan o‘chirish
async def delete_after_delay(chat_id, message_id, delay):
    await asyncio.sleep(delay)
    await bot.delete_message(chat_id, message_id)


# Lichkadan yoki guruhdan /start bosilganda salomlashuv xabarini yuboradi
@group_router.message(Command("start"))
async def start_command(message: types.Message):
    text = (
        "👋 Assalomu alaykum!\n\n"
        "Men guruhingizni tartibga solishda yordam beruvchi botman.\n\n"
        "*Mening imkoniyatlarim:*\n"
        "📌 *KANALGA OBUNA SHART* - Foydalanuvchilar kanalga a’zo bo‘lmaguncha yozish huquqiga ega bo‘lmaydi.\n\n"
        "👥 *GURUHGA ODAM TAKLIF QILISH* - Foydalanuvchilar ma’lum miqdordagi odamni guruhga taklif qilmaguncha yozishlari cheklanadi.\n\n"
        "🗑 *KIRDI-CHIQTI XABARLARINI O‘CHIRISH* - Guruhga kim qo‘shilgani yoki chiqib ketgani haqidagi xabarlarni avtomatik o‘chirib boraman.\n\n"
        "⛔️ *REKLAMA VA SPAMGA QARSHI HIMOYA* - Guruhingizni nomaqbul reklama va spamdan himoya qilaman.\n\n"
        "🔞 *SO‘KINISH VA HAQORATLARNI O‘CHIRISH* - Axloqsiz va haqoratli so‘zlarni aniqlab, ularni avtomatik o‘chiraman.\n\n"
        "🚫 *KANAL NOMIDAN YOZISHNI TAQIQLASH* - Foydalanuvchilarning kanal nomidan yozishiga ruxsat bermayman.\n\n"
        "🔹 Botni guruhingizga qo‘shib, tartibni ta’minlang!"
    )

    # Inline tugma yaratish
    start_button = InlineKeyboardButton(
        text="➕ Guruhga qo‘shish ➕",
        url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[start_button]])

    sent_message = await message.reply(
        text=text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

    asyncio.create_task(delete_after_delay(message.chat.id, sent_message.message_id, 60))


# Guruhni faollashtirish
@group_router.message(Command("activate"))
async def activate_group(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        chat = message.chat
        user = message.from_user
        bot_member = await message.bot.get_chat_member(chat.id, message.bot.id)

        chat_admins = await message.bot.get_chat_administrators(chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]

        if not bot_member.status in [ChatMemberStatus.ADMINISTRATOR]:
            await message.reply(
                "🚫 Bot guruhda admin emas!\n\n"
                "Botga quyidagi ruxsatlarni bering:\n"
                "✅ Xabarlarni o‘chirish\n"
                "✅ Foydalanuvchilarni cheklash (ban qilish)\n"
                "✅ Xabarlarni pin qilish\n"
                "✅ Xabar yuborish va o‘zgartirish\n\n"
                "Botni *administrator* qilib, ushbu ruxsatlarni bering va /activate buyrug'ini yuboring!",
                parse_mode="Markdown"
            )
            return

        if user.id not in admin_ids:
            await message.reply(
                NOT_ADMIN_TEXT
            )
            return

        _group = await Group.get_or_create(chat_id=message.chat.id, title=message.chat.title)
        if not _group.is_activate:
            await _group.activate()
            await message.reply(
                "✅ Guruh muvaffaqiyatli faollashtirildi!\n"
                f"🏷 Guruh nomi: <a href='tg://user?id={_group.chat_id}'>#{_group.title}</a>",
                parse_mode="HTML"
            )
            return

        await message.reply(
            "⚠️ Guruh allaqachon faollashtirilgan!\n\n"
            "Guruhni botdan ajratish uchun /deactivate buyrug'ini yuboring.\n\n"
            f"🏷 Guruh nomi: <a href='tg://user?id={_group.chat_id}'>#{_group.title}</a>",
            parse_mode="HTML"
        )
    else:
        await message.reply(
            "❌ Bu buyruq faqat guruhlarda ishlaydi!\n\n"
            "ℹ️ Botni faollashtirish uchun, guruh ichida /activate buyrug'ini yuboring."
        )


# Guruhni deaktivatsiyalash (Botdan ajratish)
@group_router.message(Command("deactivate"))
async def deactivate_group(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        chat = message.chat
        user = message.from_user

        chat_admins = await message.bot.get_chat_administrators(chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]
        bot_member = await message.bot.get_chat_member(chat.id, message.bot.id)

        if not bot_member.status in [ChatMemberStatus.ADMINISTRATOR]:
            await message.reply(
                "🚫 Bot guruhda admin emas!\n\n"
                "Botga quyidagi ruxsatlarni bering:\n"
                "✅ Xabarlarni o‘chirish\n"
                "✅ Foydalanuvchilarni cheklash (ban qilish)\n"
                "✅ Xabarlarni pin qilish\n"
                "✅ Xabar yuborish va o‘zgartirish\n\n"
                "Botni *administrator* qilib, ushbu ruxsatlarni bering va /deactivate buyrug'ini yuboring!",
                parse_mode="Markdown"
            )
            return

        if user.id not in admin_ids:
            await message.reply(
                NOT_ADMIN_TEXT
            )
            return

        _group = await Group.get_or_create(message.chat.id, message.chat.title)
        if _group.is_activate:
            await _group.activate()
            await message.reply(
                "✅ Guruh muvaffaqiyatli deaktivatsiya qilindi!\n\n"
                f"🔹 Guruh nomi: <a href='tg://user?id={_group.chat_id}'>#{_group.title}</a>\n\n"
                "ℹ️ Botni qayta faollashtirish uchun /activate buyrug'ini yuboring.",
                parse_mode="HTML"
            )

            return

        await message.reply(
            "⚠️ Guruh allaqachon deaktivatsiya qilingan!\n\n"
            "🔹 Guruhni botga qayta ulash uchun /activate buyrug'ini yuboring.\n\n"
            f"📌 Guruh nomi: <a href='tg://user?id={_group.chat_id}'>#{_group.title}</a>",
            parse_mode="HTML"
        )

    else:
        await message.reply(
            "⚠️ /deactivate buyrug‘idan faqat guruhlarda foydalanish mumkin!",
        )


# Guruhga kanalni bog'lash
@group_router.message(Command("add"))
async def add_channel(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        chat = message.chat
        user = message.from_user

        _group = await Group.get_or_create(message.chat.id, message.chat.title)
        if not _group.is_activate:
            await message.reply(
                "❌ Bot hali guruhga ulanmagan.\n\n"
                "🔗 Botni guruhga ulash uchun quyidagi buyruqni yuboring:\n"
                "/activate",
                parse_mode="Markdown"
            )
            return

        chat_admins = await message.bot.get_chat_administrators(chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]
        bot_member = await message.bot.get_chat_member(chat.id, message.bot.id)

        if not bot_member.status in [ChatMemberStatus.ADMINISTRATOR]:
            await message.reply(
                "🚫 Bot guruhda admin emas!\n\n"
                "Botga quyidagi ruxsatlarni bering:\n"
                "✅ Xabarlarni o‘chirish\n"
                "✅ Foydalanuvchilarni cheklash (ban qilish)\n"
                "✅ Xabarlarni pin qilish\n"
                "✅ Xabar yuborish va o‘zgartirish\n\n"
                "Botni *administrator* qilib, ushbu ruxsatlarni bering va `/add @channel_username` buyrug'ini yuboring!",
                parse_mode="Markdown"
            )
            return

        if user.id not in admin_ids:
            await message.reply(
                NOT_ADMIN_TEXT
            )
            return

        command_args = message.text.split()
        if len(command_args) < 2:
            await message.reply(
                "ℹ️ Iltimos, buyruq bilan birga kanal username-ni ham yuboring.\n\n"
                "📌 Misol: `/add @channel_username`",
                parse_mode="Markdown"
            )

        if _group.required_channel:
            channel = await message.bot.get_chat(_group.required_channel)
            await message.reply(
                f"📢 Guruh allaqachon [ {channel.title} ](https://t.me/{channel.username.lstrip('@')}) kanaliga ulangan.\n\n"
                "➖ Yangi kanal qo‘shish uchun avval /removeChannel buyrug‘ini yuborib, avvalgi kanalni ajrating.",
                parse_mode="Markdown"
            )
            return

        channel_username = command_args[1]

        try:
            channel = await message.bot.get_chat(channel_username)
            bot_in_channel = await message.bot.get_chat_member(channel.id, message.bot.id)

            if bot_in_channel.status in [ChatMemberStatus.ADMINISTRATOR]:

                await _group.add_channel(channel.id)
                await message.reply(
                    f"✅ [ {channel.title} ](https://t.me/{channel_username.lstrip('@')}) kanali guruhga muvaffaqiyatli qo‘shildi!",
                    parse_mode="Markdown"
                )

            else:
                await message.reply(
                    f"🚫 Bot {channel_username} kanalida admin emas!\n\n"
                    "Botni kanalga admin qilib, quyidagi ruxsatlarni bering:\n"
                    "✅ Post joylash\n"
                    "✅ Postlarni o‘chirish\n"
                    "✅ Obunachilarni boshqarish\n\n"
                    "So‘ng, qaytadan `/add @channel_username` buyrug'ini yuboring!",
                    parse_mode="Markdown"
                )

        except Exception as e:
            await message.reply(
                "❌ Kanal topilmadi yoki bot kanalga qo‘shilmagan.\n\n"
                "ℹ️ Iltimos, botni kanalingizga *admin* sifatida qo‘shing va qaytadan urinib ko‘ring!",
                parse_mode="Markdown"
            )


# Guruhni kanaldan ajratish
@group_router.message(Command("removeChannel"))
async def remove_channel(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        chat = message.chat
        user = message.from_user

        _group = await Group.get_or_create(message.chat.id, message.chat.title)
        if not _group.is_activate:
            await message.reply(
                "❌ Bot hali guruhga ulanmagan.\n\n"
                "🔹 Botni guruhga ulash uchun /activate buyrug‘idan foydalaning."
            )
            return

        chat_admins = await message.bot.get_chat_administrators(chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]
        bot_member = await message.bot.get_chat_member(chat.id, message.bot.id)

        if not bot_member.status in [ChatMemberStatus.ADMINISTRATOR]:
            await message.reply(
                "🚫 Bot guruhda admin emas!\n\n"
                "Botga quyidagi ruxsatlarni bering:\n"
                "✅ Xabarlarni o‘chirish\n"
                "✅ Foydalanuvchilarni cheklash (ban qilish)\n"
                "✅ Xabarlarni pin qilish\n"
                "✅ Xabar yuborish va o‘zgartirish\n\n",
                parse_mode="Markdown"
            )
            return

        if user.id not in admin_ids:
            await message.reply(
                NOT_ADMIN_TEXT
            )
            return

        if _group.required_channel:
            channel = await message.bot.get_chat(_group.required_channel)
            await _group.remove_channel(channel.id)
            await message.reply(
                f"📢 Guruh [ {channel.title} ](https://t.me/{channel.username[1:]}) kanalidan uzildi.\n\n"
                f"➖ Yangi kanal qo‘shish uchun avval `/add @channel_username` buyrug‘ini yuborib yangi kanal qo'shishingiz mumkin",
                parse_mode="Markdown"
            )
            return

        await message.reply(
            "❌ Guruhga hali hech qanday kanal ulanmadi.\n\n"
            "➕ Yangi kanal qo‘shish uchun quyidagi buyruqni yuboring:\n"
            "`/add @channel_username`",
            parse_mode="Markdown"
        )
