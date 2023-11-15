from aiogram.fsm.state import State, StatesGroup


class BotState(StatesGroup):
    select_game = State()
    playing_guess_facts = State()
    playing_guess_flag = State()
