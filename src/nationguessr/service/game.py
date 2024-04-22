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


def number_as_emoji(num: int, slots: int = 5) -> str:
    """Converts the digits of a positive integer into their equivalent emoji characters.

    The function uses a mapping of digits from 0 to 9 to their corresponding emoji characters.
    Conversion is performed per digit from right to left using base-10 division strategy of `num`.

    Args:
        num (int): The positive integer to be converted into emoji.
        slots (int): The minimum number of emoji characters in the output. If the number of digits
            in `num` is less than `slots`, the result is left-padded with '0' characters.

    Returns:
        str: A string representation of the number using emoji characters for each digit.

    Raises:
        ValueError: If input integer value is negative or if the minimum number of emoji characters is less than 1.

    Examples:
        >>> number_as_emoji(123)
        '1️⃣2️⃣3️⃣'
        >>> number_as_emoji(405, slots=6)
        '0️⃣0️⃣0️⃣4️⃣0️⃣5️⃣'
        >>> number_as_emoji(0)
        '0️⃣'
        >>> try:
        ...     number_as_emoji(-1)
        ... except ValueError as e:
        ...     print(e)
        The input integer value must be positive

    Note:
        - Emoji character mapping is defined in the function body.
    """

    if num < 0:
        raise ValueError("The input integer value must be positive")
    elif slots < 1:
        raise ValueError("The minimum number of emoji characters must be at least 1")

    emoji_map = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]

    if num == 0:
        return emoji_map[0] * max(
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

        emoji_number = emoji_map[last_digit] + emoji_number

    if (
        num_base < slots
    ):  # Left pad result with extra zeros if its length is less than slots number
        emoji_number = emoji_map[0] * (slots - num_base) + emoji_number

    return emoji_number


def draw_game_bar(session: GameSession, settings: Settings, bar_gap: int = 20) -> str:
    health_bar = "❤️" * session.lives_remained + "💔" * (
        settings.default_init_lives - session.lives_remained
    )
    score_bar = number_as_emoji(session.current_score)

    return health_bar + " " * bar_gap + score_bar


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
