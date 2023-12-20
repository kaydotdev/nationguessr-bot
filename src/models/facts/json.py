import json
import os
import random
from typing import List

from .base import CountryCode, FactsGeneratorBase


class JSONReservoirSamplingGenerator(FactsGeneratorBase):
    def __init__(
        self, file_path: str | os.PathLike, country_code: CountryCode, sample_size: int
    ) -> None:
        super().__init__(country_code, sample_size)

        self._file_handler = open(file_path)

    def generate(self) -> List[str]:
        file_content = json.load(self._file_handler)
        country_facts = file_content.get(self._code)
        reservoir = []

        if country_facts is None:
            return []

        for index, item in enumerate(country_facts):
            if index < self._sample_size:
                reservoir.append(item)
            else:
                replace_index = random.randint(0, index)

                if replace_index < self._sample_size:
                    reservoir[replace_index] = item

        return reservoir

    def __del__(self) -> None:
        if not self._file_handler.closed:
            self._file_handler.close()
