from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery
from typing import Union
from aiogram.dispatcher import FSMContext
from tgbot.misc.films_module import get_films, get_movies
from tgbot.misc.films_module import get_url_for_film
import json
import requests

menu_cd = CallbackData("show_menu", "level", "kp_id", "current_page", "translate_id", "quality")
buy_item = CallbackData("buy", "item_id")


def make_callback_data(level, kp_id='0', current_page="1", translate_id="0", quality="0"):
    return menu_cd.new(level=level, kp_id=kp_id, current_page=current_page, translate_id=translate_id,
                       quality=quality)


async def films_keyboard(message: Union[CallbackQuery, Message], state: FSMContext, current_page=1):
    CURRENT_LEVEL = 0
    markup = InlineKeyboardMarkup()
    count_button = 0
    films = await get_films(message=message, state=state, current_page=current_page)
    for num, film in enumerate(films.data):
        button_text = f'{num + 1}) {film.ru_title} ({film.year[0:4]})'
        if film.kinopoisk_id is None:
            continue
        callback_data = make_callback_data(level=CURRENT_LEVEL + 1, kp_id=film.kinopoisk_id, current_page=current_page)
        markup.add(
            InlineKeyboardButton(text=button_text, callback_data=callback_data)
        )
        count_button += 1
    if count_button == 0:
        await message.reply(f'По Вашему запросу 🔎<b> {message.text}</b> ничего не найдено.\n'
                            f'Попробуйте  <i>заново выполнить поиск</i>, изменив запрос.')
        return 0
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
    last_translate = ''
    for translate in translates:
        button_text = ""
        if last_translate == translate.translation_id:
            continue
        with open('tgbot\\translation.json', encoding='utf-8') as json_file:
            data = json.load(json_file)
        for i in data['data']:
            if i['id'] == int(translate.translation_id):
                button_text = f"{i['shorter_title']}"

        callback_data = make_callback_data(level=CURRENT_LEVEL + 1,
                                           kp_id=kp_id,
                                           current_page=current_page,
                                           translate_id=translate.translation_id)
        markup.add(
            InlineKeyboardButton(text=button_text, callback_data=callback_data)
        )
        last_translate = translate.translation_id
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
    count_button = 0
    last_translate = ''
    for quality in qualities:
        if quality.translation_id == int(translate_id):
            if last_translate == quality.translation_id:
                continue
            for resolution in quality.qualities[:-1]:
                url = await get_url_for_film(url="http:" + resolution.url,
                                             translation_id=int(translate_id),
                                             quality=int(resolution.resolution))
                response = requests.get(url, stream=True)
                total_size = round(int(response.headers.get('content-length')) / 1073741824, 2)
                if total_size > 2 or total_size == 0.0:
                    continue
                else:
                    callback_data = make_callback_data(level=CURRENT_LEVEL + 1,
                                                       kp_id=kp_id,
                                                       current_page=current_page,
                                                       translate_id=translate_id,
                                                       quality=str(resolution.resolution))
                    markup.add(
                        InlineKeyboardButton(text=str(resolution.resolution) + f" ({str(total_size)} GB)",
                                             callback_data=callback_data)
                    )
                    count_button += 1
            last_translate = quality.translation_id
    markup.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data=make_callback_data(level=CURRENT_LEVEL - 1,
                                             kp_id=kp_id,
                                             current_page=current_page,
                                             translate_id=translate_id))
    )
    if count_button == 0:
        await callback.message.reply("Данный фильм на VideoCDN <b><i>отсутствует</i></b>.\n"
                                     "Попробуйте посмотреть с другим переводом.",
                                     reply_markup=markup)
        return 0
    return markup
