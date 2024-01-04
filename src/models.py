import json
from typing import Generator, TextIO

from pydantic import BaseModel, Field


class CountryCode(BaseModel):
    """
    Represents a country code in a standardized format ISO 3166-1 alpha-2:
    https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2.

    It inherits from BaseModel, making use of Pydantic's validation features.

    Attributes:
        code (str): A string representing the country code. This should be a
                    2-character string. The code is validated to ensure it meets
                    the specified maximum length.

    Example:
        >>> country_code = CountryCode(code="US")
        >>> print(country_code.code)
        US

    Raises:
        ValidationError: If the provided code does not conform to the expected
                         format or length constraints.
    """

    code: str = Field(..., max_length=2)


def json_fetch_country_facts(
    file_handler: TextIO, country_code: CountryCode
) -> Generator[str, None, None]:
    """Iteratively yields facts about a specified country from a JSON file.

    This function takes a file handler to a JSON file and a country code object.
    It loads the content of the JSON file using the file handler, lazy-loads
    facts based on the given country code in a form of a generator.

    Args:
        file_handler (TextIO): A file handler for the JSON file containing
            country facts. The file should be opened in a text mode and should
            contain a JSON object where each key corresponds to a country code
            and the value is a list of facts about the country.
        country_code (CountryCode): An ISO 3166-1 alpha-2 code of a corresponding
            country.

    Yields:
        Items from a random subset of the input iterator.
    """

    file_content = json.load(file_handler)
    country_facts = file_content.get(country_code.code)

    if country_facts is not None:
        yield from country_facts
