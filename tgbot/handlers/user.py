from aiogram import Dispatcher
from tgbot.keyboards.keyboard_button import menu
from aiogram.dispatcher import filters, FSMContext
from aiogram.types import CallbackQuery, Message
from tgbot.keyboards.menu_keyboards_films import menu_cd as menu_cd_films
from tgbot.misc.states import UserState
import tgbot.handlers.user_films as user_films
import tgbot.handlers.user_tv_serials as user_tv_serials


FORBIDDEN_PHRASE = [
    '🎬',
    '🎥'
]


async def show_menu(message: Message):
    await message.reply(f"Здравствуйте 👋, <b><i>{message.from_user.first_name}</i></b>")
    await message.answer("Выберете категорию поиска: ", reply_markup=menu)
    #await UserState.Category.set()


async def set_category(message: Message):
    if message.text == '🎬 Фильмы':
        await UserState.Films.set()
    if message.text == '🎥 Сериалы':
        await UserState.TV_Serials.set()
    await message.answer(f'Вы выбрали раздел {message.text}\n'
                         f'Введите название {message.text[2:-1].lower()}а для поиска')


def register_user(dp: Dispatcher):
    dp.register_message_handler(show_menu, commands=['start'], state='*')
    dp.register_message_handler(set_category, filters.Text(startswith=FORBIDDEN_PHRASE, ignore_case=True), state='*')

    dp.register_message_handler(user_films.show_results, state=UserState.Films)
    dp.register_message_handler(user_tv_serials.show_results, state=UserState.TV_Serials)

    dp.register_callback_query_handler(user_films.navigate, menu_cd_films.filter(), state=UserState.Films)
    dp.register_callback_query_handler(user_tv_serials.navigate, menu_cd_films.filter(), state=UserState.TV_Serials)
