import logging
import pandas as pd
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

BOT_TOKEN = "8128628004:AAEGqc1kIvZV-z3jh3VPkvTyWVlEEd01wLA"
SPREADSHEET_ID = "1TI1VGYBDvsRinBVHAPf1wZDvBN-rRCW_Fic6Q9-5nqA"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class UserState(StatesGroup):
    login = State()
    sheet = State()
    week = State()

# Получение списка листов Google Sheets через API gviz
async def get_sheet_names():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:json"
    try:
        text = requests.get(url).text
        json_str = text[text.find('{'):-2]
        data = eval(json_str.replace('null', 'None'))  # преобразуем в dict
        sheets = [entry['name'] for entry in data['table']['cols'] if entry]
        return sheets
    except Exception as e:
        logging.error(f"Ошибка получения : {e}")
        return []

# /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет коллега! Тут ты можешь посмотреть результаты своей работы за неделю, для этого дай мне свой логин.")
    await UserState.login.set()

# логин
@dp.message_handler(state=UserState.login)
async def get_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text.strip())
    sheets = await get_sheet_names()
    if not sheets:
        await message.answer("Не удалось получить список операций. Попробуйте позже.")
        return

    kb = InlineKeyboardMarkup(row_width=2)
    for name in sheets:
        kb.add(InlineKeyboardButton(name, callback_data=f"sheet:{name}"))

    await message.answer("Отлично! Теперь выбери операцию, которая интересует:", reply_markup=kb)
    await UserState.sheet.set()

# обработка нажатия на кнопку листа
@dp.callback_query_handler(lambda c: c.data.startswith('sheet:'), state=UserState.sheet)
async def process_sheet_selection(callback_query: types.CallbackQuery, state: FSMContext):
    sheet_name = callback_query.data.split(':')[1]
    await state.update_data(sheet=sheet_name)

    # Получаем список последних 4 недель из столбцов листа
    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(csv_url)
        week_columns = [col for col in df.columns if col.lower().startswith("w") or "неделя" in col.lower()]
        last_weeks = week_columns[-4:]
        kb = InlineKeyboardMarkup(row_width=2)
        for w in last_weeks:
            kb.add(InlineKeyboardButton(w, callback_data=f"week:{w}"))
        await bot.send_message(callback_query.from_user.id, "Спасибо! Теперь выбери неделю:", reply_markup=kb)
        await UserState.week.set()
    except Exception:
        await bot.send_message(callback_query.from_user.id, "Ошибка при получении списка недель. Введите вручную.")
        await bot.send_message(callback_query.from_user.id, "Теперь укажи название недели (например: W1).", reply_markup=ReplyKeyboardRemove())
        await UserState.week.set()

# обработка выбора недели из инлайн-кнопки
@dp.callback_query_handler(lambda c: c.data.startswith('week:'), state=UserState.week)
async def week_button(callback_query: types.CallbackQuery, state: FSMContext):
    week_col = callback_query.data.split(':')[1]
    message = types.Message(message_id=callback_query.message.message_id, from_user=callback_query.from_user)
    message.text = week_col
    await get_week(message, state)

# неделя вручную
@dp.message_handler(state=UserState.week)
async def get_week(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    login = user_data['login']
    sheet = user_data['sheet']
    week_col = message.text.strip()

    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet}"

    try:
        df = pd.read_csv(csv_url)
    except Exception:
        await message.answer("Не удалось загрузить данные по операции. Проверь название.")
        await state.finish()
        return

    login_col = df.columns[0]  # первый столбец = логины
    df[login_col] = df[login_col].astype(str)
    row = df[df[login_col].str.lower() == login.lower()]

    if row.empty:
        await message.answer("Пользователь с таким логином не найден.")
        await state.finish()
        return

    if week_col not in df.columns:
        await message.answer(f"Столбец с названием '{week_col}' не найден.")
        await state.finish()
        return

    result = row.iloc[0]
    response = f"<b>Лист:</b> {sheet}
<b>Логин:</b> {login}

"
    for col in df.columns:
        response += f"{col}: {result[col]}
"

    await message.answer(response, parse_mode="HTML")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)