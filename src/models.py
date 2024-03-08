from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, Field, NonNegativeInt, StrictStr


class BotReplicaView(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9]{24}$")
    key: StrictStr
    replica: StrictStr


class CountryFactView(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9]{24}$")
    tags: List[StrictStr]
    content: StrictStr


class CountryNameView(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9]{24}$")
    code: str = Field(..., max_length=2)
    name: StrictStr


class ScoreBoard(BaseModel):
    records: Dict[datetime, NonNegativeInt]


class GameSession(BaseModel):
    lives_remained: NonNegativeInt
    current_score: NonNegativeInt
    options: List[StrictStr]
    correct_option: StrictStr
