from typing import Dict, List

from pydantic import BaseModel, NonNegativeInt, StrictStr


class GameSession(BaseModel):
    score_board: Dict[StrictStr, NonNegativeInt]
    lives_remained: NonNegativeInt
    current_score: NonNegativeInt
    options: List[StrictStr]
    correct_option: StrictStr


class FactsGuessingGameRound(BaseModel):
    options: List[StrictStr]
    correct_option: StrictStr
    facts: List[StrictStr]
