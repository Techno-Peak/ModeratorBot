from aiogram import Router, types
from aiogram.filters import Command
from database.models import Group

group_router = Router()

@group_router.message(Command("activate"))
async def activate_group(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        chat = message.chat
        user = message.from_user

        chat_admins = await message.bot.get_chat_administrators(chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]

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
async def activate_group(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        chat = message.chat
        user = message.from_user

        chat_admins = await message.bot.get_chat_administrators(chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]

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