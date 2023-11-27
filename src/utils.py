from itertools import islice

from aiogram.fsm.context import FSMContext
from models import ScoreBoard


async def validate_and_fetch_scores(state: FSMContext) -> ScoreBoard:
    """Reads and validates user score history from an abstract key-value database.
    History records are queried for a specific active user by ID.

    Args:
        state (FSMContext): abstract application state storage.

    Returns:
        ScoreBoard: Validated user score history.

    Raises:
        ValidationError: Failed to validate FSM state due to the possible data corruption.
    """

    state_data = await state.get_data()
    score_data = state_data.get("scores", {})

    return ScoreBoard(records=score_data)


def batched(iterable, n):
    if n < 1:
        raise ValueError("n must be at least one")

    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch
