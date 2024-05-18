import csv
import json
import logging
import math
import os
import random
import zipfile
from abc import ABC, abstractmethod
from datetime import datetime
from io import BytesIO, StringIO
from typing import List, Tuple

import aiofiles
import aiohttp

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
        >>> number_as_character(12345)
        '12345'
        >>> number_as_character(405, slots=6)
        '000405'
        >>> number_as_character(0)
        '00000'
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
    """Records a new score into the session's scoreboard and resets the current score to zero.
    Keeps only the top number of scores, as specified in the settings, along with the corresponding
    dates of score achievements.

    Args:
        session (GameSession): An instance of a game session containing the current score and scoreboard.
        settings (Settings): An application settings instance specifying the number of top scores to display
                             on the scoreboard.

    Returns:
        GameSession: The updated game session instance with the new score recorded and the current score reset.

    Note:
        - This function returns a new session instance without modifying the values of the provided one.
    """

    new_session = GameSession(**session.model_dump())
    score_timestamp = datetime.utcnow().strftime("%d/%m/%Y")

    current_score = new_session.current_score
    new_session.current_score = 0

    if len(new_session.score_board.items()) < settings.default_top_scores:
        new_session.score_board.update({current_score: score_timestamp})
    elif any(score <= current_score for score in new_session.score_board.keys()):
        if current_score not in new_session.score_board:
            least_valuable_score = min(new_session.score_board.keys())
            new_session.score_board.pop(least_valuable_score)

        new_session.score_board[current_score] = score_timestamp

    return new_session


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


class GenerationFromGptStrategy(FactGenerationStrategy):
    def __init__(
        self, settings: Settings, fallback_strategy: FactGenerationStrategy
    ) -> None:
        if not settings.openai_api_token:
            raise AttributeError("No OpenAI API credentials available")

        self._settings = settings
        self._ai_model_name = "gpt-4o"
        self._system_prompt = (
            "You are a Nationguessr AI, an artificial intelligence that is specialized in interesting facts about "
            f"counties worldwide. Your goal is to generate {settings.default_facts_num} interesting facts about a "
            "particular country, based on the name provided, so the user will try to guess this country. Your facts "
            "should be interesting and cover culture, its ancient history, unique places to visit and about its "
            "people. Each fact should be a one sentence long. Do not include obvious facts, such as the name of "
            "the capital or the name of the currency. Do not write a name of the country directly in the facts, "
            "instead substitute the name with phrase 'this country'. You must not provide facts that somewhat "
            "related to politics, war or other sensitive topics. When writing output facts, you must always follow "
            "a template structure, which is a JSON object with a key being an index of generated fact (starting from "
            '1) and a value being a fact itself:\n\n{\n    "1": "1st fact",\n    "2": "2nd fact",\n    ...\n}'
        )
        self._logger = logging.getLogger(self.__class__.__name__)
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.openai_api_token}",
        }
        self._fallback_strategy = fallback_strategy

    async def generate_facts(self, country_code: str) -> List[str]:
        async with aiofiles.open(
            os.path.join(self._settings.assets_folder, "data", "countries.csv"),
            mode="r",
        ) as file:
            reader = csv.reader(
                StringIO(await file.read()), delimiter=",", quotechar='"'
            )
            selected_country = next(
                _name for _, _code, _name in reader if _code == country_code
            )

        request_body = {
            "model": self._ai_model_name,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": selected_country},
            ],
            "temperature": 1.0,
            "max_tokens": 1024,
        }

        async with aiohttp.ClientSession() as client:
            async with client.post(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(request_body),
                headers=self._headers,
            ) as response:
                response_body = await response.text()

                if response.status != 200:
                    err_response = json.loads(response_body).get("error", {})
                    err_msg = err_response.get("message", "")

                    self._logger.error(
                        f"An error occurred while sending the request to OpenAI API: '{err_msg}'"
                    )
                    return await self._fallback_strategy.generate_facts(country_code)

        assistant_choices = json.loads(response_body).get("choices")

        if not assistant_choices:
            self._logger.error(
                f"The OpenAI API returned an invalid response for the chosen country "
                f"'{selected_country}': {assistant_choices}"
            )
            return await self._fallback_strategy.generate_facts(country_code)

        generated_facts = assistant_choices[0].get("message")

        if not generated_facts:
            self._logger.error(
                f"Received an empty generated list of facts for the country '{selected_country}' from "
                f"the OpenAI API"
            )
            return await self._fallback_strategy.generate_facts(country_code)

        parsed_facts = list(json.loads(generated_facts.get("content", "{}")).values())

        if len(parsed_facts) != self._settings.default_facts_num:
            self._logger.error(
                f"Received a generated list of facts for the country '{selected_country}' with invalid "
                f"number of facts. Expected {self._settings.default_facts_num}, received "
                f"{len(parsed_facts)}"
            )
            return await self._fallback_strategy.generate_facts(country_code)

        return parsed_facts


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
