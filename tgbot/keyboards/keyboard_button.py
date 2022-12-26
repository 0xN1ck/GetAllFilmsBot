from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🎬 Фильмы"),
            KeyboardButton(text="🎥 Сериалы")
        ],
    ],
    resize_keyboard=True
)
