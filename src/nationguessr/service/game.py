import csv
import math
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


def number_as_character(
    num: int, slots: int = 5, char_map: List[str] | None = None
) -> str:
    """Converts the digits of a positive integer into their equivalent ASCII or Unicode characters.
    The list of characters that correspond to digits 0-9 should be provided in `char_map`; otherwise,
    the default ASCII representation ["0" - "9"] is used. The element index from 0 to 9 should map to the
    character that represents a digit, and the number of elements must be equal to the number of digits
    0-9, which is 10.

    Conversion is performed per digit from right to left using the base-10 division strategy of `num`.

    Args:
        num (int): The positive integer to be converted into characters.
        slots (int): The minimum number of character slots in the output. If the number of digits
            in `num` is less than `slots`, the result is left-padded with '0' characters.
        char_map (List[str] | None, optional): A list of characters that map to the digits 0-9.
            If not provided, the default ASCII representation ["0" - "9"] is used.

    Returns:
        str: A string representation of the number using the specified characters for each digit.

    Raises:
        ValueError: If the input integer value is negative.
        ValueError: If the minimum number of character slots is less than 1.
        ValueError: If the number of elements in `char_map` does not equal 10.

    Examples:
        >>> number_as_character(123)
        '123'
        >>> number_as_character(405, slots=6)
        '000405'
        >>> number_as_character(0)
        '0'
        >>> try:
        ...     number_as_character(-1)
        ... except ValueError as e:
        ...     print(e)
        The input integer value must be positive
        >>> emoji_map = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
        >>> number_as_character(123, char_map=emoji_map)
        '1️⃣2️⃣3️⃣'
    """

    if num < 0:
        raise ValueError("The input integer value must be positive")

    if slots < 1:
        raise ValueError("The minimum number of emoji characters must be at least 1")

    char_map = (
        ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        if char_map is None
        else char_map
    )

    if len(char_map) != 10:
        raise ValueError(
            "The number of elements in `char_map` must correspond to the number of digits 0-9, i.e., equal 10."
        )

    if num == 0:
        return char_map[0] * max(
            1, slots
        )  # Ensure that even '0' has the minimum number of characters

    emoji_number = ""
    num_base = (
        math.floor(math.log10(num)) + 1
    )  # Calculate the number of digits in the input integer

    while num > 0:
        last_digit = num % 10
        num //= (
            10  # Remove last digit from remaining digits sequence of the input integer
        )

        emoji_number = char_map[last_digit] + emoji_number

    if (
        num_base < slots
    ):  # Left pad result with extra zeros if its length is less than slots number
        emoji_number = char_map[0] * (slots - num_base) + emoji_number

    return emoji_number


def record_new_score(session: GameSession, settings: Settings) -> GameSession:
    recorded_scores = session.score_board.keys()
    top_recorded_scores = sorted(recorded_scores, reverse=True)[
        : settings.default_top_scores
    ]

    if len(recorded_scores) >= settings.default_top_scores and all(
        score > session.current_score for score in top_recorded_scores
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
            os.path.join(self._settings.assets_folder, "data", "country_facts.zip"),
            mode="rb",
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
            os.path.join(self._settings.assets_folder, "data", "countries.csv"),
            mode="r",
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
