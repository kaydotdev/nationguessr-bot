from aiogram.fsm.context import FSMContext
from models import ScoreBoard


async def validate_and_fetch_scores(state: FSMContext) -> ScoreBoard:
    state_data = await state.get_data()
    score_data = state_data.get("scores", {})

    return ScoreBoard(records=score_data)
