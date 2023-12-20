from abc import ABC, abstractmethod
from typing import List

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


class FactsGeneratorBase(ABC):
    def __init__(self, country_code: CountryCode, sample_size: int):
        self._code = country_code.code
        self._sample_size = sample_size

    @abstractmethod
    def generate(self) -> List[str]:
        raise NotImplementedError("Facts generation is available for subclasses only.")
