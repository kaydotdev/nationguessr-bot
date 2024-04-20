import csv
import os
import random
import zipfile
from abc import ABC, abstractmethod
from datetime import datetime
from io import BytesIO, StringIO
from typing import List, Tuple

import aiofiles

from ..data.game import FactsGuessingGameRound, GameSession
from ..service.utils import reservoir_sampling
from ..settings import Settings


def record_new_score(session: GameSession, settings: Settings) -> GameSession:
    recorded_scores = session.score_board.keys()

    if len(recorded_scores) >= settings.default_top_scores and all(
        score > session.current_score for score in recorded_scores
    ):
        return session

    score_timestamp = datetime.utcnow().strftime("%d/%m/%Y")
    current_score = session.current_score

    session.score_board.update({current_score: score_timestamp})
    session.current_score = 0

    return session


class FactGenerationStrategy(ABC):
    @abstractmethod
    async def generate_facts(self, country_code: str) -> List[str]:
        raise NotImplementedError("Facts generation is available for subclasses only.")


class GenerationFromZipStrategy(FactGenerationStrategy):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate_facts(self, country_code: str) -> List[str]:
        async with aiofiles.open(
            os.path.join(self._settings.assets_folder, "country_facts.zip"), mode="rb"
        ) as file:
            with zipfile.ZipFile(BytesIO(await file.read())) as facts_zip:
                with facts_zip.open(f"{country_code}.csv") as facts_file:
                    facts_content = (
                        line.decode("utf-8") for line in facts_file.readlines()
                    )
                    reader = csv.reader(facts_content, delimiter=",", quotechar='"')
                    selected_facts = [
                        fact
                        for _, _, fact in reservoir_sampling(
                            reader, self._settings.default_facts_num
                        )
                    ]

        return selected_facts


class GuessingFactsGameService:
    def __init__(self, strategy: FactGenerationStrategy, settings: Settings) -> None:
        self._strategy = strategy
        self._settings = settings

    async def _select_random_options(self) -> List[Tuple[str, str]]:
        selected_country_ids = random.sample(
            list(range(1, self._settings.default_countries_num + 1)),
            k=self._settings.default_options_num,
        )

        async with aiofiles.open(
            os.path.join(self._settings.assets_folder, "countries.csv"), mode="r"
        ) as file:
            reader = csv.reader(
                StringIO(await file.read()), delimiter=",", quotechar='"'
            )
            selected_country = [
                (country_code, country_name)
                for country_id, country_code, country_name in reader
                if int(country_id) in selected_country_ids
            ]

        return selected_country

    async def new_game_round(self) -> FactsGuessingGameRound:
        selected_countries = await self._select_random_options()
        correct_country = random.choice(selected_countries)
        correct_country_code, correct_country_name = correct_country

        options = [name for _, name in selected_countries]

        facts = await self._strategy.generate_facts(correct_country_code)

        return FactsGuessingGameRound(
            correct_option=correct_country_name, options=options, facts=facts
        )
