from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, NonNegativeInt, StrictStr


class ScoreBoard(BaseModel):
    records: Dict[datetime, NonNegativeInt]


class GameSession(BaseModel):
    lives_remained: NonNegativeInt
    current_score: NonNegativeInt
    options: List[StrictStr]
    correct_option: StrictStr


class FactsGuessingGameRound(BaseModel):
    options: List[StrictStr]
    correct_option: StrictStr
    facts: List[StrictStr]
