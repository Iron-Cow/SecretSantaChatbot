import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import MagicData
from aiogram.filters.command import Command
from aiogram.filters.callback_data import CallbackData
from db_manager import DbDriver
from random import randint
from keyboard_manager import KeyboardManager
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import text, bold, italic, code, pre
from states import SecretSantaStates
from aiogram.fsm.context import FSMContext
from utils import encode_room, decode_room, create_pairings
import os

token = os.getenv("TG_TOKEN")
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=token)
# Диспетчер
dp = Dispatcher()
router = Router()
kbm = KeyboardManager()


class RoomInfoCallback(CallbackData, prefix="room_info"):
    number: int = 0


class RoomDeleteCallback(CallbackData, prefix="room_delete"):
    number: int = 0


class RoomJoinCallback(CallbackData, prefix="room_join"):
    number: int = 0


class RoomAddPlayersCallback(CallbackData, prefix="room_add_player"):
    number: int = 0
    pair: bool = False


class RoomLeaveCallback(CallbackData, prefix="room_leave"):
    number: int = 0

class RoomSortCallback(CallbackData, prefix="room_sort"):
    number: int = 0


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")


# Хэндлер на команду /test1
@dp.message(Command("test1"))
async def cmd_test1(message: types.Message):
    try:
        db = DbDriver()
        db.insert_room(message.from_user.id)
    except Exception as e:
        # Handle exceptions (e.g., log them, send a message to the user)
        await message.reply(f"Виникла помилка: {e}")
    finally:
        db.close()

    await message.reply("Test 1")


@dp.message(Command("help"))
async def cmd_test1(message: types.Message):
    buttons = [
        [InlineKeyboardButton(text="Список кімнат", callback_data="room_list")],
        [InlineKeyboardButton(text="Приєднатись до кімнати", callback_data="room_join")]
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.reply("Обирай:", reply_markup=kb)


@dp.callback_query(F.data.contains("room_join"))
async def join_room_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    await state.set_state(SecretSantaStates.join_group)
    await bot.send_message(callback.from_user.id,
                           text=text("Введіть код запрошення до кімнати. (Наприклад => secretsanta-....)",
                                     "(без кавичок)"))
    buttons = [
        [InlineKeyboardButton(text="Скасувати", callback_data="cancel")]
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(callback.from_user.id, text=text("... або натистіть 'Скасувати')"), reply_markup=kb)


@dp.message(SecretSantaStates.join_group)
async def join_group(message: types.Message, state: FSMContext) -> None:
    try:
        room_number = decode_room(message.text.strip())
        buttons = [
            [InlineKeyboardButton(text=f"Кімната {room_number}", callback_data=RoomInfoCallback(number=room_number).pack())]
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer(f"Вітаємо в кімнаті {room_number}", reply_markup=kb)
    except ValueError as err:
        buttons = [
            [InlineKeyboardButton(text="Скасувати", callback_data="cancel")]
        ]

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await  message.answer(f"{message.text.strip()} здається мені неправильним. Спробуй ще", reply_markup=kb)


# Хэндлер на команду /test2
async def cmd_test2(message: types.Message):
    try:
        db = DbDriver()
        num = randint(1, 1000)
        rooms = db.get_all_rooms()
    except Exception as e:
        # Handle exceptions (e.g., log them, send a message to the user)
        await message.reply(f"Виникла помилка: {e}")
    finally:
        db.close()

    await message.reply(str(rooms))





@dp.callback_query(F.data == "room_list")
async def room_list(callback: types.CallbackQuery):
    try:
        db = DbDriver()
        num = randint(1, 1000)
        rooms = db.get_my_rooms(callback.from_user.id)
        buttons = []

        if not rooms:
            await bot.send_message(callback.from_user.id, "Ви ще не створили/не доєднались до жодної групи. Спробуйте /help")
            return

        for (room, owner_tg_id) in rooms:
            row_buttons = [
                InlineKeyboardButton(text=f"Кімната {room}", callback_data=RoomInfoCallback(number=room).pack())]
            if owner_tg_id == callback.from_user.id:
                row_buttons.append(
                    InlineKeyboardButton(text=f"Сортувати {room}",
                                         callback_data=RoomSortCallback(number=room).pack())
                )
                row_buttons.append(
                    InlineKeyboardButton(text=f"Видалити {room}",
                                         callback_data=RoomDeleteCallback(number=room).pack())
                )
            buttons.append(row_buttons)

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        # kb = kbm.get_inline_keyboard().row(btn)
        await bot.send_message(callback.from_user.id,"Оберіть кімнату для деталей", reply_markup=kb)

    except Exception as e:
        # Handle exceptions (e.g., log them, send a message to the user)
        await bot.send_message(callback.from_user.id,f"Виникла помилка: {e}")
    finally:
        db.close()


@dp.callback_query(F.data.contains("room_sort"))
async def room_sort(callback: types.CallbackQuery):
    await callback.answer(callback.data)  # wow
    data = RoomSortCallback().unpack(callback.data)
    try:
        db = DbDriver()
        members = db.get_room_players(data.number)

        pairs = create_pairings(members)
        for send_to_tg_id, from_name, from_group_name, to_name, to_group_name in pairs:
            try:
                await bot.send_message(send_to_tg_id, f'{from_name} ({from_group_name}) 🤲🎁➡️ {to_name} ({to_group_name})')
            except Exception as err:
                await bot.send_message(callback.from_user.id, f"Виникла помилка: {err}")

    except Exception as e:
        # Handle exceptions (e.g., log them, send a message to the user)
        await bot.send_message(callback.from_user.id, f"Виникла помилка: {e}")
    finally:
        db.close()



@dp.callback_query(F.data.contains("room_info"))
async def room_info(callback: types.CallbackQuery):
    await callback.answer(callback.data)  # wow
    data = RoomInfoCallback().unpack(callback.data)

    try:
        db = DbDriver()
        members = db.get_room_players(data.number)

    except Exception as e:
        # Handle exceptions (e.g., log them, send a message to the user)
        await bot.send_message(callback.from_user.id, f"Виникла помилка: {e}")
    finally:
        db.close()

    players = ""
    is_in_game = False
    for member, pair, tg_id in members:
        if tg_id == callback.from_user.id:
            is_in_game = True
        if pair:
            for pair_member in member.split(" "):
                players += f"🎄 {pair_member}({member})\n"
        else:
            players += f"🎄 {member}\n"
    buttons = []
    buttons.append(
        [InlineKeyboardButton(text=f"Покинути кімнату {data.number}",
                              callback_data=RoomLeaveCallback(number=data.number).pack())]
    )
    if not is_in_game:
        buttons.append(
            [
                InlineKeyboardButton(text=f"Додати гравця до кімнати {data.number}",
                                     callback_data=RoomAddPlayersCallback(number=data.number, pair=False).pack()),
                InlineKeyboardButton(text=f"Додати пару до кімнати {data.number}",
                                     callback_data=RoomAddPlayersCallback(number=data.number, pair=True).pack()),
            ]
        )
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(callback.from_user.id, text="Активні гравці:")
    if players:
        await bot.send_message(callback.from_user.id, text=players, reply_markup=kb)
    else:
        await bot.send_message(callback.from_user.id, text="(Поки немає гравців)", reply_markup=kb)


@dp.callback_query(F.data.contains("room_add_player"))
async def add_players_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    data = RoomAddPlayersCallback().unpack(callback.data)
    await state.update_data(room=data.number)
    if data.pair:
        await state.set_state(SecretSantaStates.add_pair)
        await bot.send_message(callback.from_user.id,
                               text=text("Введіть 2 імені гравців через пробіл. (Наприклад => ", code("Юра Неля"),
                                         "(без кавичок)"))
    else:
        await state.set_state(SecretSantaStates.add_player)
        await bot.send_message(callback.from_user.id, text=text("Введіть імʼя одинокого гравця. (Лише імʼя)"))

    buttons = [
        [InlineKeyboardButton(text="Скасувати", callback_data="cancel")]
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(callback.from_user.id, text=text("... або натистіть 'Скасувати')"), reply_markup=kb)


@dp.callback_query(F.data == "cancel")
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await bot.send_message(callback.from_user.id, text=text("Скасовано. Спробуйте /help."))


@dp.message(SecretSantaStates.add_player)
async def add_player(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    try:
        db = DbDriver()
        db.add_player(message.text, tg_id=message.from_user.id, pair=False, room_id=data.get("room", -1))
        await state.set_state(None)
        await  message.answer(f"Гравця {message.text} додано в  кімнату {data.get('room', -1)}")


    except Exception as e:
        # Handle exceptions (e.g., log them, send a message to the user)
        await message.answer(f"Виникла помилка: {e}")
    finally:
        db.close()


@dp.message(SecretSantaStates.add_pair)
async def add_pair(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = message.text.strip().split(" ")
    if len(pair) != 2:
        buttons = [
            [InlineKeyboardButton(text="Скасувати", callback_data="cancel")]
        ]

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await  message.answer(
            f"Введені дані для пари ({' + '.join(pair)}) виглядают не правильно :(. \nПотрібно ввести 2 імʼя через пробіл. Cпробуй ще",
            reply_markup=kb)
        return
    try:
        db = DbDriver()
        db.add_player(message.text, tg_id=message.from_user.id, pair=True, room_id=data.get("room", -1))
        await state.set_state(None)
        await  message.answer(f"Гравців {' + '.join(pair)} додано в  кімнату {data.get('room', -1)}")


    except Exception as e:
        # Handle exceptions (e.g., log them, send a message to the user)
        await message.answer(f"Виникла помилка: {e}")
    finally:
        db.close()


@dp.callback_query(F.data.contains("room_leave"))
async def leave_room(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    data = RoomLeaveCallback().unpack(callback.data)
    try:
        db = DbDriver()
        db.leave_room(tg_id=callback.from_user.id, room_id=data.number)
        await state.set_state(None)
        await bot.send_message(callback.from_user.id,
                               f"Ви покинули кімнату {data.number}. Спробуйте знайти сенс життя з /help")

    except Exception as e:
        # Handle exceptions (e.g., log them, send a message to the user)
        await bot.send_message(callback.from_user.id, f"Виникла помилка: {e}")
    finally:
        db.close()


# Запуск процесса поллинга новых апдейтов
async def main():
    dp.message.register(cmd_test2, Command("test2"))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
