import asyncio
import re
from telebot.types import Message
from aiogram.dispatcher import filters, FSMContext
from aiogram.types import CallbackQuery, Message
from typing import Union
from tgbot.keyboards.menu_keyboards_films import films_keyboard, translates_keyboard, qualities_keyboard
from tgbot.misc.films_module import get_info_film, get_movies, get_url_for_film, download_film, send_film
import os


async def show_results(message: Message, state: FSMContext):
    await state.update_data(search=message.text)
    await list_films(message, state)


async def list_films(message: Union[CallbackQuery, Message], state: FSMContext, current_page="1", **kwargs):
    if isinstance(message, Message):
        markup = await films_keyboard(message, state)
        if markup:
            await message.answer(f"Вот, что у нас есть по Вашему запросу \n"
                                 f"🔎<b> {message.text}</b>", reply_markup=markup)
    elif isinstance(message, CallbackQuery):
        call = message
        markup = await films_keyboard(call, state, current_page=int(current_page))
        if markup:
            await call.message.edit_reply_markup(markup)


async def list_translates(callback: CallbackQuery, kp_id, current_page="1", **kwargs):
    markup = await translates_keyboard(callback, kp_id, current_page)
    info = await get_info_film(token_kp=callback.bot.data['config'].token_kp, kp_id=kp_id)
    genres = ', '.join([genre.genre for genre in info['genres']])
    await callback.message.answer_photo(photo=info['photo'],
                                        caption=f"<i>Название: </i ><b>{info['name']} ({info['year']})\n</b>"
                                                f"<i>Жанры: </i> <b>{genres}\n</b>"
                                                f"<i>Продолжительность:</i> <b>{info['duration']} мин.</b>\n\n"
                                                f"{info['description']}\n\n"
                                                f"<i>Рейтинг Кинопоиск:</i> <b>{info['rating_kp']}</b>\n"
                                                f"<i>Рейтинг IMDb:</i> <b>{info['rating_imdb']}</b>",
                                        reply_markup=markup)
    # Изменяем сообщение, и отправляем новые кнопки с подкатегориями


async def list_qualities(callback: CallbackQuery, kp_id, current_page, translate_id, **kwargs):
    markup = await qualities_keyboard(callback, kp_id, current_page, translate_id)
    if markup:
        await callback.message.edit_reply_markup(markup)


async def get_film(callback: CallbackQuery, kp_id, current_page, translate_id, quality, **kwargs):
    data = await get_movies(callback, kp_id)

    for movies in data:
        if movies.translation_id == int(translate_id):
            for resolution in movies.qualities:
                if resolution.resolution == int(quality):
                    url = await get_url_for_film(url='http:' + movies.path,
                                                 translation_id=translate_id,
                                                 quality=quality)
                    name = callback.message.caption.split("\n")[0].split("Название: ")[-1].strip()
                    name = re.sub(r'["<>«»*:?|]', '', name)
                    path = f'films\\{name + "_" + str(quality) + "_" + str(translate_id) + ".mp4"}'
                    loop = asyncio.get_event_loop()
                    asyncio.set_event_loop(loop)
                    if not os.path.exists(path):
                        mes = await callback.message.answer(text="Фильм скачивается на сервер")
                        await asyncio.to_thread(download_film, callback, url, path, mes, loop, callback.bot)
                        await mes.answer("Фильм скачан на сервер, теперь отправляем его Вам.")
                    else:
                        mes = await callback.message.answer("Фильм есть на сервер, отправляем его Вам.")
                    await asyncio.to_thread(send_film, callback, path, loop, callback.bot, mes.chat.id)
                    break
            break


async def navigate(call: CallbackQuery, callback_data: dict, state: FSMContext):
    """

    :param state:
    :param call: Тип объекта CallbackQuery, который прилетает в хендлер
    :param callback_data: Словарь с данными, которые хранятся в нажатой кнопке
    """

    # Получаем текущий уровень меню, который запросил пользователь
    current_level = callback_data.get("level")

    # Получаем категорию, которую выбрал пользователь (Передается всегда)
    kp_id = callback_data.get("kp_id")

    translate_id = callback_data.get("translate_id")

    current_page = callback_data.get("current_page")

    quality = callback_data.get("quality")

    levels = {
        "0": list_films,  # Отдаем категории
        "1": list_translates,  # Отдаем подкатегории
        "2": list_qualities,
        "3": get_film,
    }

    # Забираем нужную функцию для выбранного уровня
    current_level_function = levels[current_level]

    # Выполняем нужную функцию и передаем туда параметры, полученные из кнопки
    await current_level_function(
        call,
        kp_id=kp_id,
        current_page=current_page,
        translate_id=translate_id,
        quality=quality,
        state=state,
    )

