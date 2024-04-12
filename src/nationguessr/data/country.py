from typing import List

from pydantic import BaseModel, Field, StrictStr


class CountryFactView(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9]{24}$")
    tags: List[StrictStr]
    content: StrictStr


class CountryNameView(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9]{24}$")
    code: str = Field(..., max_length=2)
    name: StrictStr
