from aiogram.fsm.state import State, StatesGroup


class AddCh(StatesGroup):
    wait = State()


class Create(StatesGroup):
    channel = State()
    title = State()
    thumb = State()
    pbtn = State()
    support = State()


class Join(StatesGroup):
    name = State()
    photo = State()
