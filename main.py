import os
from aiogram import *
from aiogram.types import ParseMode
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from dotenv import load_dotenv
from videocdn_tv import VideoCDN, ParamsContent

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
bot = Bot(os.environ.get("TOKEN_BOT"))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

videoCDN = VideoCDN(api_token=os.environ.get("TOKEN_VIDEOCDN"))


class UserState(StatesGroup):
    category = State()


@dp.message_handler(commands=["start"])
async def start_message(message: types.Message):
    chat_id = message.chat.id
    kb = [
        [
            types.KeyboardButton(text="Фильмы", ),
            types.KeyboardButton(text='Сериалы')
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await bot.send_message(chat_id, 'Выберете, что вы будете искать: фильм или сериал?', reply_markup=keyboard)
    await UserState.category.set()


@dp.message_handler(state=UserState.category)
async def text_message(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if message.text == 'Фильмы':
        await state.update_data(category=message.text)
        await bot.send_message(chat_id, f'Вы выбрали раздел <b>{message.text}</b>\n'
                                        f'Введите название для поиска', parse_mode=ParseMode.HTML)
    elif message.text == 'Сериалы':
        await bot.send_message(chat_id, f"Раздел Сериалы находится в разработке, выберете, пожалуйста, другой")
        return
    category = await state.get_data()
    data = videoCDN.get_movies(ParamsContent(query=message.text))
    try:
        if category['category'] == 'Фильмы':
            for movie in data.data:
                await bot.send_message(chat_id, f'Название : <b>{movie.ru_title}</b>\n'
                                                f'Ссылка для просмотра : {movie.preview_iframe_src}',
                                                parse_mode=ParseMode.HTML)
    except KeyError:
        await bot.send_message(chat_id, f'Вы не выбрали раздел. Чтобы выполнить поиск, выберите раздел')


if __name__ == '__main__':
    executor.start_polling(dp)
