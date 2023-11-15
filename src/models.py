from typing import Dict, List
from datetime import datetime
from pydantic import BaseModel, NonNegativeInt, StrictStr


class ScoreBoard(BaseModel):
    records: Dict[datetime, NonNegativeInt]


class GameSession(BaseModel):
    lives_remained: NonNegativeInt
    current_score: NonNegativeInt
    options: List[StrictStr]
    correct_option: StrictStr
