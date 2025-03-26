import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from database.models import BlockedWord, User, Group
from config import bot
from handlers.utils import delete_after_delay, AUTO_DELETE_TIME_INTERVAL, delete_message

admin_router = Router()


@admin_router.message(Command('words'))
async def list_blocked_words(message: Message):
    if message.chat.type == 'private':
        from_user = message.from_user

        user = await User.get_user(chat_id=from_user.id)

        if not (user and user.is_admin):
            await message.reply(
                text="⚠️ Ushbu buyruqdan faqat <b>adminlar</b> foydalanishi mumkin!\n\n",
                parse_mode="HTML"
            )
            return

        blocked_words = await BlockedWord.get_blocked_words()

        if not blocked_words:
            await message.reply(
                text="📌 Bloklangan so‘zlar ro‘yxati bo‘sh.",
                parse_mode="HTML"
            )
            return

        chunk_size = 15  # Har bir xabarda 15 ta so‘z yuboramiz
        for i in range(0, len(blocked_words), chunk_size):
            words_chunk = blocked_words[i:i + chunk_size]  # 15 tadan ajratamiz
            words_text = "\n".join([f"🔹 <b>{word}</b> - <code>/word {word}</code>" for word in words_chunk])  # Ro‘yxat ko‘rinishida chiqaramiz

            await message.reply(
                text=f"📌 Bloklangan so‘zlar:\n\n{words_text}\n\n"
                     "🗑 O‘chirish uchun: <code>/word so‘z_nomi</code>",
                parse_mode="HTML"
            )

    else:
        sm = await message.bot.send_message(
            chat_id=message.chat.id,
            text="ℹ️ <b>/words</b> buyrug‘idan faqat bot bilan shaxsiy chatda foydalanish mumkin.\n\n"
                 "Iltimos, ushbu buyruqni botga shaxsiy xabarda yuboring.",
            parse_mode="HTML"
        )
        asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))
        await delete_message(message)


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
            # ❌ O‘chirish tugmasi bilan inline klaviatura yaratamiz
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"delete_word:{new_word}")]
                ]
            )
            await message.reply(
                text=f"⚠️ <b>{new_word[0]}...{new_word[-1]}</b> so‘zi allaqachon bloklangan!",
                parse_mode="HTML",
                reply_markup=keyboard
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


@admin_router.callback_query(lambda c: c.data.startswith("delete_word:"))
async def delete_blocked_word(callback: CallbackQuery):
    word_to_delete = callback.data.split(":")[1]  # Callbackdan so‘zni olamiz

    # So‘zni bazadan o‘chiramiz
    deleted = await BlockedWord.delete(word_to_delete)

    if deleted:
        await callback.message.edit_text(
            text=f"✅ <b>{word_to_delete[0]}...{word_to_delete[-1]}</b> so‘zi bloklanganlar ro‘yxatidan olib tashlandi!",
            parse_mode="HTML"
        )
        await callback.answer("O‘chirildi ✅")
    else:
        await callback.answer("⚠️ So‘z topilmadi yoki allaqachon o‘chirilgan!", show_alert=True)



@admin_router.message(Command('guruh'))
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
                     "📌 Faqat guruh administratorlari <b>/guruh</b> buyrug‘idan foydalanishi mumkin.",
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
                     "Agar odam qo'shishni o'chirmoqchi bo'lsangiz <code>/guruh 0</code> buyrug'idan foydalaning\n\n"
                     "📌 Misol: <code>/guruh 5</code>",
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
                         "<code>/guruh [yangi son]</code>\n\n"
                         "❌ Agar bu talabni o‘chirmoqchi bo‘lsangiz, quyidagi buyruqni yuboring:\n"
                         "<code>/guruh 0</code>",
                    parse_mode="HTML"
                )
            else:
                sm = await message.bot.send_message(
                    chat_id=message.chat.id,
                    text="✅ Guruhga majburiy qo‘shilish talabi bekor qilindi.\n\n"
                         "📌 Endi foydalanuvchilar cheklovsiz yozishlari mumkin.\n\n"
                         "✏️ Agar bu talabni qayta yoqmoqchi bo‘lsangiz, yangi limitni quyidagi formatda kiriting:\n"
                         "<code>/guruh [yangi son]</code>",
                    parse_mode="HTML"
                )
        else:
            sm = await message.bot.send_message(
                chat_id=message.chat.id,
                text="❌ Noto‘g‘ri format! Iltimos, faqat raqam kiriting.\n\n"
                     "✅ To‘g‘ri foydalanish namunasi:\n"
                     "<code>/guruh 5</code>",
                parse_mode="HTML"
            )
        asyncio.create_task(delete_after_delay(sm.chat.id, sm.message_id, AUTO_DELETE_TIME_INTERVAL))
        await delete_message(message)

    else:
        sm = await message.bot.send_message(
            chat_id=message.chat.id,
            text="ℹ️ <b>/guruh</b> buyrug‘idan faqat guruhlarda foydalanish mumkin.\n\n"
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

        if not target_user:
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

        if target_user.is_super_admin:
            await message.reply(
                text=f"ℹ️Siz <b><a href=\"tg://user?id={target_user.chat_id}\">{target_full_name}</a></b> ni adminlar safidan "
                     f"chiqarolmaysiz!",
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


@admin_router.message(Command('adminlar'))
async def show_admins(message: Message):
    if message.chat.type == 'private':
        from_user = message.from_user

        user = await User.get_user(chat_id=from_user.id)

        if not (user and user.is_admin):
            await message.reply(
                text="⚠️ Ushbu buyruqdan faqat <b>adminlar</b> foydalanishi mumkin!",
                parse_mode="HTML"
            )
            return

        # Barcha adminlarni bazadan olish
        admins = await User.get_admins()

        if not admins:
            await message.reply("🚫 Hozircha hech qanday admin yo'q.")
            return

        admin_list = []
        for idx, admin in enumerate(admins):
            chat = await message.bot.get_chat(admin.chat_id)  # Telegram'dan to'g'ri ismni olish
            admin_name = chat.full_name  # To‘liq ism (first_name + last_name)

            admin_list.append(
                f"{idx + 1}. User: <a href=\"tg://user?id={admin.chat_id}\">{admin_name}</a> \n"
                f"  Adminlar safidan o'chirish: <code>/remove_admin {admin.chat_id}</code>\n"
            )

        await message.reply(
            text=f"👮‍♂️ <b>Adminlar ro'yxati:</b>\n\n" + "\n".join(admin_list),
            parse_mode="HTML"
        )
    else:
        await delete_message(message)


@admin_router.message(Command('add_super_admin'))
async def add_admin(message: Message):
    if message.chat.type == 'private':
        command_args = message.text.split(maxsplit=1)
        try:
            target_id = int(command_args[1].strip())
        except ValueError:
            return

        # Foydalanuvchini ID orqali topamiz
        target_user = await User.get_user(chat_id=target_id)

        # Adminlikni yangilaymiz
        await target_user.update_is_admin(True, True)

        await message.reply(
            text=f"✅ Ok!",
            parse_mode="HTML"
        )


admin_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📩 Xabar yuborish")],
                [KeyboardButton(text="📊 Statistika")],
                [KeyboardButton(text="Chiqish")],
            ],
            resize_keyboard=True
        )

@admin_router.message(Command('admin'))
async def welcomeAdminpanel(message: Message):
    user_id = message.from_user.id
    user = await User.get_user(user_id)
    if message.chat.type == 'private' and user.is_admin:
        await message.answer(
            "📌 *Admin panelga xush kelibsiz!*\n\n👇 Quyidagi tugma orqali xabar yuborishingiz mumkin:",
            reply_markup=admin_keyboard,
            parse_mode="Markdown"
        )
    else:
        await delete_message(message)


class SendMessageState(StatesGroup):
    waiting_for_message = State()
    waiting_for_choice = State()


@admin_router.message(F.text == "Chiqish")
async def sendMessageTypes(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await User.get_user(user_id)

    if message.chat.type == 'private' and user.is_admin:
        await message.answer(
            "📌 *Admin paneldan chiqdingiz*",

            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(remove_keyboard=True)
        )
    else:
        await delete_message(message)


@admin_router.message(F.text == "📊 Statistika")
async def sendMessageTypes(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await User.get_user(user_id)

    if message.chat.type == 'private' and user.is_admin:
        group_count = await Group.get_group_count()
        private_user_count = await User.get_private_user_count()

        await message.answer(
            f"📌 Bot statistikasi\n\n"
            f"📊 Guruhlar soni: <b>{group_count}</b>\n"
            f"👤 Foydalanuvchilar soni: <b>{private_user_count}</b>",
            reply_markup=admin_keyboard,
            parse_mode="HTML"
        )
    else:
        await delete_message(message)


@admin_router.message(F.text == "📩 Xabar yuborish")
async def sendMessageTypes(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await User.get_user(user_id)

    reply_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="❌ Bekor qilish")]
            ],
            resize_keyboard=True
        )
    
    if message.chat.type == 'private' and user.is_admin:
        await message.answer(
            "📌 *Yubormoqchi bo'lgan xabaringizni kiriting yoki forward qiling!*",
            reply_markup=reply_keyboard,
            parse_mode="Markdown"
        )
        await state.set_state(SendMessageState.waiting_for_message)
    else:
        await delete_message(message)
    

@admin_router.message(F.text == "❌ Bekor qilish")
async def sendMessageTypes(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await User.get_user(user_id)

    if message.chat.type == 'private' and user.is_admin:
        await state.clear()
        await message.answer(
            "📌 *Bekor qilindi!*",
            reply_markup=admin_keyboard,
            parse_mode="Markdown"
        )

    else:
        await delete_message(message)


@admin_router.message(SendMessageState.waiting_for_message)
async def getMessage(message: Message, state: FSMContext):
    if message.forward_from or message.forward_from_chat:
        await state.update_data(forward_message=message)
    else:
        await state.update_data(text_message=message.text)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Guruhlarga"), KeyboardButton(text="👤 Foydalanuvchilarga")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
    
    await message.answer("📌 Xabarni kimga yubormoqchisiz?", reply_markup=keyboard)
    
    await state.set_state(SendMessageState.waiting_for_choice)


@admin_router.message(SendMessageState.waiting_for_choice, F.text.in_(["📢 Guruhlarga", "👤 Foydalanuvchilarga"]))
async def forwardOrSendMessage(message: Message, state: FSMContext):
    data = await state.get_data()
    forward_message = data.get("forward_message")
    text_message = data.get("text_message")
    users = await User.get_private_users()
    groups = await Group.get_all_groups()

    target_users = []
    target_groups = []
    
    if message.text == "📢 Guruhlarga":
        target_groups = [group.chat_id for group in groups]
        target = "📢 Guruhlarga yuborildi!"
    else:
        target_users = [user.chat_id for user in users]
        target = "👤 Foydalanuvchilarga yuborildi!"
    
    async def send_to_target(chat_id):
        try:
            await asyncio.sleep(0.1)
            if forward_message:
                await forward_message.forward(chat_id=chat_id)
            elif text_message:
                await bot.send_message(chat_id=chat_id, text=text_message)
            return (chat_id, True)
        except Exception:
            return (chat_id, False)
    
    tasks = [send_to_target(chat_id) for chat_id in target_users + target_groups]
    results = await asyncio.gather(*tasks)

    success_count = sum(1 for _, success in results if success)
    failed_count = sum(1 for _, success in results if not success)

    await message.answer(
        f"✅ *Xabaringiz muvaffaqiyatli {target}*\n\n"
        f"📨 Yuborilganlar: {success_count}\n"
        f"⚠️ Yuborilmaganlar: {failed_count}",
        parse_mode="Markdown",
        reply_markup=admin_keyboard
    )

    await state.clear()


