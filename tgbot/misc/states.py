from aiogram.dispatcher.filters.state import StatesGroup, State


class UserState(StatesGroup):
    Category = State()
    Film_name = State()
