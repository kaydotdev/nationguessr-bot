from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage


class BotState(StatesGroup):
    select_game = State()
    playing_guess_facts = State()
    playing_guess_flag = State()


state_storage = MemoryStorage()
