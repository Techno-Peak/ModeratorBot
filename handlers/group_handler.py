from aiogram import Router, types
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command
from database.models import Group

group_router = Router()

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
            await message.reply("Bu buyruq faqat adminlar uchun!")
            return

        _group = await Group.get_or_create(chat_id=message.chat.id, title=message.chat.title)
        if not _group.is_activate:
            await _group.activate()
            await message.reply(
                "Guruh muvaffaqiyatli activate qilindi\n"
                f"Guruh nomi: <a href='tg://user?id={_group.chat_id}'>#{_group.title}</a>",
                parse_mode="HTML"
            )
            return

        await message.reply(
            "Guruh allaqachon activate qilingan\n"
            "Guruhni botdan ajratish uchun /deactivate buyrug'ini yuboring\n"
            f"Guruh nomi: <a href='tg://user?id={_group.chat_id}'>#{_group.title}</a>",
            parse_mode="HTML"
        )
    else:
        await message.reply("/activate buyrug'i faqat guruhlarda ishlaydi")


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
            await message.reply("Bu buyruq faqat adminlar uchun!")
            return

        _group = await Group.get_or_create(chat_id=message.chat.id, title=message.chat.title)
        if _group.is_activate:
            await _group.activate()
            await message.reply(
                "Guruh muvaffaqiyatli deactivate qilindi\n"
                f"Guruh nomi: <a href='tg://user?id={_group.chat_id}'>#{_group.title}</a>",
                parse_mode="HTML"
            )
            return

        await message.reply(
            "Guruh allaqachon deactivate qilingan\n"
            "Guruhni botga ulash uchun /activate buyrug'ini yuboring\n"
            f"Guruh nomi: <a href='tg://user?id={_group.chat_id}'>#{_group.title}</a>",
            parse_mode="HTML"
        )
    else:
        await message.reply("/deactivate buyrug'i faqat guruhlarda ishlaydi")


@group_router.message(Command("add"))
async def add_channel(message: types.Message):
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
                "Botni *administrator* qilib, ushbu ruxsatlarni bering va `/add @channel_username` buyrug'ini yuboring!",
                parse_mode="Markdown"
            )
            return

        if user.id not in admin_ids:
            await message.reply("Bu buyruq faqat adminlar uchun!")
            return

        command_args = message.text.split()
        if len(command_args) < 2:
            await message.reply(
                "Iltimos, buyruq bilan birga kanal username ni ham yuboring.\nMisol: `/add @channel_username`",
                parse_mode="Markdown")
            return

        _group = await Group.get_or_create(message.chat.id, message.chat.title)

        if _group.required_channel:
            channel = await message.bot.get_chat(_group.required_channel)
            await message.reply(
                f"📢 Guruh [ {channel.title} ](https://t.me/{channel.username[1:]}) kanaliga ulangan.\n\n"
                f"Id: `{channel.id}`\n"
                f"➖ Yangi kanal qo‘shish uchun avval `/remove_channel` buyrug‘ini yuborib, avvalgi kanalni ajrating.",
                parse_mode="Markdown"
            )
            return

        channel_username = command_args[1]

        try:
            channel = await message.bot.get_chat(channel_username)
            bot_in_channel = await message.bot.get_chat_member(channel.id, message.bot.id)

            if bot_in_channel.status in [ChatMemberStatus.ADMINISTRATOR]:

                await message.reply(
                    f"✅ Bot [ {channel.title} ](https://t.me/{channel_username[1:]}) kanalida admin!"
                    f"Id: `{channel.id}`\n",
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
                "❌ Kanal topilmadi yoki bot kanalda emas. Iltimos, botni kanalingizga qo‘shib, qaytadan urinib ko‘ring!")
