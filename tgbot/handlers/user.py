from aiogram.dispatcher.filters import Command
from aiogram import Dispatcher
from telebot.types import Message

from tgbot.keyboards.keyboard_button import menu
from aiogram.dispatcher import filters, FSMContext
from aiogram.types import CallbackQuery, Message
from typing import Union

from tgbot.keyboards.menu_keyboards import films_keyboard, translates_keyboard, menu_cd
from tgbot.misc.states import UserState

from tgbot.misc.films_module import get_info_film

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


async def list_films(message: Union[CallbackQuery, Message], state: FSMContext, **kwargs):
    if isinstance(message, Message):
        markup = await films_keyboard(message, state)
        await message.answer(f"Вот, что у нас есть по Вашему запросу \n"
                             f"🔎<b> {message.text}</b>", reply_markup=markup)
    elif isinstance(message, CallbackQuery):
        call = message
        markup = await films_keyboard(call, state, current_page=int(call.data.split(":")[3]))
        await call.message.edit_reply_markup(markup)


async def list_translates(callback: CallbackQuery, kp_id, **kwargs):
    markup = await translates_keyboard(callback, kp_id)
    # await callback.message.delete()
    info = await get_info_film(token_kp=callback.bot.data['config'].token_kp, kp_id=kp_id)
    await callback.message.answer_photo(photo=info['photo'],
                                        caption=f"<i>Название: </i ><b>{info['name']}</b>\n\n"
                                                f"{info['description']}\n\n"
                                                f"<i>Рейтинг Кинопоиск:</i> <b>{info['rating_kp']}</b>\n"
                                                f"<i>Рейтинг IMDb:</i> <b>{info['rating_imdb']}</b>",
                                        reply_markup=markup)
    # Изменяем сообщение, и отправляем новые кнопки с подкатегориями


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

    levels = {
        "0": list_films,  # Отдаем категории
        "1": list_translates,  # Отдаем подкатегории
    }

    # Забираем нужную функцию для выбранного уровня
    current_level_function = levels[current_level]

    # Выполняем нужную функцию и передаем туда параметры, полученные из кнопки
    await current_level_function(
        call,
        kp_id=kp_id,
        current_page=current_page,
        translate_id=translate_id,
        state=state,
    )


def register_user(dp: Dispatcher):
    dp.register_message_handler(show_menu, commands=['start'], state='*')
    # dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_message_handler(set_category, filters.Text(startswith=FORBIDDEN_PHRASE, ignore_case=True),
                                state=UserState.Category)
    dp.register_message_handler(show_results, state=UserState.Category)
    dp.register_callback_query_handler(navigate, menu_cd.filter(), state=UserState.Category)
