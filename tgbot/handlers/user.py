import re

from aiogram.dispatcher.filters import Command
from aiogram import Dispatcher
from telebot.types import Message

from tgbot.keyboards.keyboard_button import menu
from aiogram.dispatcher import filters, FSMContext
from aiogram.types import CallbackQuery, Message
from typing import Union

from tgbot.keyboards.menu_keyboards import films_keyboard, translates_keyboard, qualities_keyboard, menu_cd
from tgbot.misc.states import UserState

from tgbot.misc.films_module import get_info_film, get_movies, get_url_for_film

import asyncio, requests, io
from tqdm import tqdm
from pyffmpeg import FFprobe
from pprint import pprint
import os

# async def user_start(message: Message):
#     await message.reply("Hello, user!")

FORBIDDEN_PHRASE = [
    '🎬',
    '🎥'
]


async def show_menu(message: Message):
    await message.reply("Hello, user!")
    await message.answer("Выберете категорию поиска: ", reply_markup=menu)
    await UserState.Category.set()


async def set_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    async with state.proxy() as data:
        await message.answer(f'Вы выбрали раздел {data["category"]}\n'
                             f'Введите название {data["category"][2:-1].lower()}а для поиска')


async def show_results(message: Message, state: FSMContext):
    # await UserState.Film_name.set()
    await state.update_data(search=message.text)
    async with state.proxy() as data:
        if data["category"] == '🎬 Фильмы':
            await list_films(message, state)
        elif data["category"] == '🎥 Сериалы':
            print('later')


async def list_films(message: Union[CallbackQuery, Message], state: FSMContext, current_page="1", **kwargs):
    if isinstance(message, Message):
        markup = await films_keyboard(message, state)
        await message.answer(f"Вот, что у нас есть по Вашему запросу \n"
                             f"🔎<b> {message.text}</b>", reply_markup=markup)
    elif isinstance(message, CallbackQuery):
        call = message
        markup = await films_keyboard(call, state, current_page=int(current_page))
        await call.message.edit_reply_markup(markup)


async def list_translates(callback: CallbackQuery, kp_id, current_page="1", **kwargs):
    markup = await translates_keyboard(callback, kp_id, current_page)
    # await callback.message.delete()
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
    # print(max_quality)
    markup = await qualities_keyboard(callback, kp_id, current_page, translate_id)
    await callback.message.edit_reply_markup(markup)


async def get_film(callback: CallbackQuery, kp_id, current_page, translate_id, quality, **kwargs):
    data = await get_movies(callback, kp_id)
    mes = await callback.message.answer(text="Фильм скачивается на сервер")
    for movies in data:
        if movies.translation_id == int(translate_id):
            for resolution in movies.qualities:
                if resolution.resolution == int(quality):
                    url = await get_url_for_film(url='http:' + movies.path,
                                                 translation_id=translate_id,
                                                 quality=quality)
                    path = f'films\\{(url[url.find("?dn=")+4:-4]+"_"+str(translate_id)+".mp4")}'
                    print(path, os.path.exists(path))
                    if not os.path.exists(path):
                        with open(path, "wb") as video:
                            response = requests.get(url, stream=True)
                            total_size_in_bytes = int(response.headers.get('content-length', 0))
                            block_size = 1024
                            name = callback.message.caption.split("\n")[0].split(":")[-1].strip()
                            percent_total = io.StringIO()
                            percent_current = 10
                            progress_bar = tqdm(file=percent_total, total=total_size_in_bytes, unit='iB', unit_scale=True,
                                                mininterval=0.1)
                            with open(path, 'wb') as file:
                                for data in response.iter_content(block_size):
                                    percent_total.truncate(0)
                                    percent_total.seek(0)
                                    progress_bar.update(len(data))
                                    file.write(data)
                                    result = percent_total.getvalue().split("\n")[-1].strip()
                                    if int(progress_bar.last_print_n / total_size_in_bytes * 100) >= percent_current:
                                        print(result, len(result))
                                        await mes.edit_text(f"*Фильм скачан на:* \n"
                                                            f"{result}",
                                                            parse_mode='MARKDOWN')
                                        percent_current += 10
                            progress_bar.close()
                            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                                print("ERROR, something went wrong")
                        await mes.answer("Фильм скачан на сервер, теперь отправляем его Вам.")
                    else:
                        await mes.answer("Фильм есть на сервер, отправляем его Вам.")
                    with open(path, "rb") as video:
                        #thumb = await callback.bot.get_file(callback.message.photo[2].file_id)
                        name = callback.message.caption.split("\n")[0].split(":")[-1].strip()
                        duration = int(re.findall('\\d+', callback.message.caption.split("\n")[2])[0]) * 60
                        width_height = FFprobe(path).metadata[0][0]['dimensions']
                        width = int(width_height.split('x')[0])
                        height = int(width_height.split('x')[1])
                        await callback.message.answer_video(video=video,
                                                            duration=duration,
                                                            caption=f"{name}",
                                                            #thumb=open(thumb.file_path, 'rb'),
                                                            width=width,
                                                            height=height,
                                                            supports_streaming=True,
                                                            )
                        await asyncio.sleep(10)
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


def register_user(dp: Dispatcher):
    dp.register_message_handler(show_menu, commands=['start'], state='*')
    # dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_message_handler(set_category, filters.Text(startswith=FORBIDDEN_PHRASE, ignore_case=True),
                                state=UserState.Category)
    dp.register_message_handler(show_results, state=UserState.Category)
    dp.register_callback_query_handler(navigate, menu_cd.filter(), state=UserState.Category)
