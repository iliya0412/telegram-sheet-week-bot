# Telegram Bot: Google Sheets Weekly Reporter

Этот бот позволяет сотрудникам просматривать данные за конкретную неделю из Google Sheets, выбрав логин, лист и неделю.

## 📦 Установка

```bash
git clone https://github.com/<your-username>/telegram-sheet-week-bot.git
cd telegram-sheet-week-bot
pip install -r requirements.txt
```

## 🚀 Запуск

1. Укажите токен бота и ID таблицы в `bot.py`.
2. Запустите:

```bash
python bot.py
```

## 🔒 Конфигурация

Замените в `bot.py`:
```python
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID"
```

## 🔗 Google Таблица

Формат:
- Первый столбец — логины
- Остальные — недели вида `W1`, `W2` или содержащие "Неделя"
- Несколько листов с разной структурой

## 🧠 Возможности

- Инлайн-кнопки для выбора листа и недели
- Поддержка ввода недели вручную
- Поддержка обновляемых таблиц Google Sheets
