from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery
from typing import Union
from aiogram.dispatcher import FSMContext

from tgbot.misc.films_module import get_films, get_movies, get_info_film

import json

menu_cd = CallbackData("show_menu", "level", "kp_id", "current_page", "translate_id", "quality")
buy_item = CallbackData("buy", "item_id")


def make_callback_data(level, kp_id='0', current_page="1", translate_id="0", quality="0"):
    return menu_cd.new(level=level, kp_id=kp_id, current_page=current_page, translate_id=translate_id,
                       quality=quality)


async def films_keyboard(message: Union[CallbackQuery, Message], state: FSMContext, current_page=1):
    CURRENT_LEVEL = 0
    markup = InlineKeyboardMarkup()
    films = await get_films(message=message, state=state, current_page=current_page)
    for num, film in enumerate(films.data):
        button_text = f'{num + 1}) {film.ru_title} ({film.year[0:4]})'
        if film.kinopoisk_id is None:
            continue
        callback_data = make_callback_data(level=CURRENT_LEVEL + 1, kp_id=film.kinopoisk_id, current_page=current_page)
        markup.add(
            InlineKeyboardButton(text=button_text, callback_data=callback_data)
        )
    if films.last_page > 1:
        pagination(markup, current_page, films.last_page)
    return markup


def pagination(markup, current_page: int, last_page: int):
    callback_data_next = make_callback_data(level=0, current_page=current_page + 1)
    callback_data_back = make_callback_data(level=0, current_page=current_page - 1)
    callback_data_current = make_callback_data(level=0, current_page=1)
    if current_page == 1:
        markup.row(
            InlineKeyboardButton(text=f"Page: {current_page}/{last_page}", callback_data=callback_data_current),
            InlineKeyboardButton(text="Next", callback_data=callback_data_next),
        )
    elif current_page == last_page:
        markup.row(
            InlineKeyboardButton(text="Back", callback_data=callback_data_back),
            InlineKeyboardButton(text=f"Page: {current_page}/{last_page}", callback_data=callback_data_current),
        )
    else:
        markup.row(
            InlineKeyboardButton(text="Back", callback_data=callback_data_back),
            InlineKeyboardButton(text=f"Page: {current_page}/{last_page}", callback_data=callback_data_current),
            InlineKeyboardButton(text="Next", callback_data=callback_data_next),
        )


async def translates_keyboard(callback: CallbackQuery, kp_id, current_page):
    # Текущий уровень - 1
    CURRENT_LEVEL = 1
    markup = InlineKeyboardMarkup()

    translates = await get_movies(callback, kp_id)
    for translate in translates:
        button_text = ""
        with open('tgbot\\translation.json', encoding='utf-8') as json_file:
            data = json.load(json_file)
        for i in data['data']:
            if i['id'] == int(translate.translation_id):
                button_text = f"{i['shorter_title']}"

        callback_data = make_callback_data(level=CURRENT_LEVEL + 1,
                                           kp_id=kp_id,
                                           current_page=current_page,
                                           translate_id=translate.translation_id)
        markup.insert(
            InlineKeyboardButton(text=button_text, callback_data=callback_data)
        )
    markup.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data=make_callback_data(level=CURRENT_LEVEL - 1, current_page=current_page)
        )
    )
    return markup


async def qualities_keyboard(callback: CallbackQuery, kp_id, current_page, translate_id):
    CURRENT_LEVEL = 2
    markup = InlineKeyboardMarkup()
    qualities = await get_movies(callback, kp_id)

    for quality in qualities:
        if quality.translation_id == int(translate_id):
            for resolution in quality.qualities[:-1]:
                callback_data = make_callback_data(level=CURRENT_LEVEL + 1,
                                                   kp_id=kp_id,
                                                   current_page=current_page,
                                                   translate_id=translate_id,
                                                   quality=str(resolution.resolution))
                markup.insert(
                    InlineKeyboardButton(text=str(resolution.resolution), callback_data=callback_data)
                )

    markup.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data=make_callback_data(level=CURRENT_LEVEL - 1,
                                             kp_id=kp_id,
                                             current_page=current_page,
                                             translate_id=translate_id))
    )
    return markup

# for subcategory in subcategories:
#     # Чекаем в базе сколько товаров существует под данной подкатегорией
#     number_of_items = await count_items(category_code=category, subcategory_code=subcategory.subcategory_code)
#
#     # Сформируем текст, который будет на кнопке
#     button_text = f"{subcategory.subcategory_name} ({number_of_items} шт)"
#
#     # Сформируем колбек дату, которая будет на кнопке
#     callback_data = make_callback_data(level=CURRENT_LEVEL + 1,
#                                        category=category, subcategory=subcategory.subcategory_code)
#     markup.insert(
#         InlineKeyboardButton(text=button_text, callback_data=callback_data)
#     )
#
# # Создаем Кнопку "Назад", в которой прописываем колбек дату такую, которая возвращает
# # пользователя на уровень назад - на уровень 0.
# markup.row(
#     InlineKeyboardButton(
#         text="Назад",
#         callback_data=make_callback_data(level=CURRENT_LEVEL - 1))
# )
