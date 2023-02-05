from aiogram.dispatcher.filters.state import StatesGroup, State


class UserState(StatesGroup):
    Category = State()
    Films = State()
    TV_Serials = State()
