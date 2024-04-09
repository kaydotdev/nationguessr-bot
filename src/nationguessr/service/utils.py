from itertools import islice
from sqlite3 import Cursor
from typing import Generator, Iterable, List, TypeVar

from ..data.models import CountryFactView, CountryNameView

T = TypeVar("T")


def batched(iterable: Iterable[T], n: int) -> Generator[tuple, None, None]:
    """Divide an iterable into smaller iterables of size n.

    This function takes any iterable and returns a generator yielding batches
    of the iterable's items in tuples of size n. It continues until all items from the
    original iterable have been returned in batches. If there are not enough items to
    make a final batch of exactly n items, it will return the remaining items as a smaller batch.

    Args:
        iterable (Iterable): The iterable to divide into batches.
        n (int): The desired batch size. Must be at least 1.

    Yields:
        Batches (tuples) of the original iterable's items.

    Example:
        >>> list(batched([1, 2, 3, 4, 5], 2))
        [(1, 2), (3, 4), (5,)]

    Note:
        - TODO: Replace this function with the built-in `itertools.batched` after an update to the Python 3.12 version.
        - This function is a generator and needs to be iterated over to retrieve the batches.
        - The function raises a ValueError if 'n' is less than 1 because a batch size must be positive.
    """
    if n < 1:
        raise ValueError("Batches size must be at least 1")

    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


def select_random_country_options(_cursor: Cursor, _size: int) -> List[CountryNameView]:
    _cursor.execute(
        """
        SELECT id, code, name FROM country_names
        ORDER BY RANDOM() LIMIT :size;
    """,
        {"size": _size},
    )

    return [
        CountryNameView(id=_id, code=_code, name=_name)
        for _id, _code, _name in _cursor.fetchall()
    ]


def select_random_country_facts(
    _cursor: Cursor, _name: str, _size: int
) -> List[CountryFactView]:
    """

    Args:
        _cursor:
        _name:
        _size:

    Returns:

    """

    _cursor.execute(
        """
        SELECT cf.id, cf.tags, cf.content FROM country_facts cf
        JOIN country_names cn on cf.country_id = cn.id
        WHERE cn.name = :name ORDER BY RANDOM() LIMIT :size;
    """,
        {"name": _name, "size": _size},
    )

    return [
        CountryFactView(id=_id, tags=_tags.split("|"), content=_content)
        for _id, _tags, _content in _cursor.fetchall()
    ]
