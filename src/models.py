import json
import os
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Generator, List

from pydantic import BaseModel, NonNegativeInt, StrictStr


class ScoreBoard(BaseModel):
    records: Dict[datetime, NonNegativeInt]


class GameSession(BaseModel):
    lives_remained: NonNegativeInt
    current_score: NonNegativeInt
    options: List[StrictStr]
    correct_option: StrictStr


class FactRetrievalStrategy(ABC):
    @abstractmethod
    def retrieve(self, country_code: str) -> Generator[str, None, None]: ...


class JsonFileRetrievalStrategy(FactRetrievalStrategy):
    def __init__(self, file_path: str | os.PathLike) -> None:
        self.file_handler = open(file_path)

    def retrieve(self, country_code: str) -> Generator[str, None, None]:
        file_content = json.load(self.file_handler)
        country_facts = file_content.get(country_code, [])

        return iter(country_facts)

    def __del__(self) -> None:
        if not self.file_handler.closed:
            self.file_handler.close()


class FactQuizGenerator:
    _facts = []
    _options = []
    _correct_option = ""

    def __init__(
        self,
        country_names: Dict[str, str],
        fact_retrieval_strategy: FactRetrievalStrategy,
        facts_num: int = 5,
        options_num: int = 4,
    ) -> None:
        self.country_names = country_names
        self.fact_retrieval_strategy = fact_retrieval_strategy
        self.facts_num = facts_num
        self.options_num = options_num

    @property
    def facts(self) -> List[str]:
        return self._facts

    @property
    def options(self) -> List[str]:
        return self._options

    @property
    def correct_option(self) -> str:
        return self._correct_option

    def generate(self) -> None:
        selected_country_codes = random.sample(
            self.country_names.keys(), self.options_num
        )
        selected_correct_code = random.choice(selected_country_codes)

        self._options = [
            self.country_names.get(code) for code in selected_country_codes
        ]
        self._correct_option = self.country_names.get(selected_correct_code)
        self._facts = random.sample(
            list(self.fact_retrieval_strategy.retrieve(selected_correct_code)),
            self.facts_num,
        )
