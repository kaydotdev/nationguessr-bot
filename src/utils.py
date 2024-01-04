import random
from itertools import islice
from typing import Generator, Iterable, TypeVar

from aiogram.fsm.context import FSMContext
from state import ScoreBoard

T = TypeVar("T")


async def validate_and_fetch_scores(state: FSMContext) -> ScoreBoard:
    """Reads and validates user score history from an abstract key-value database.
    History records are queried for a specific active user by ID.

    Args:
        state (FSMContext): abstract application state storage.

    Returns:
        ScoreBoard: Validated user score history.

    Raises:
        ValidationError: Failed to validate FSM state due to the possible data corruption.
    """

    state_data = await state.get_data()
    score_data = state_data.get("scores", {})

    return ScoreBoard(records=score_data)


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


def reservoir_sampling(iterator: Iterable[T], n: int) -> Generator[T, None, None]:
    """Performs reservoir sampling over an iterator and returns another iterator
    yielding a random subset of n items from the input iterator. Sampling over
    the iterator allows us to work with big sets of data without allocating them
    into memory, for instance, using lists.

    Args:
        iterator (Iterable): An iterator for the input data.
        n (int): Number of items in the output iterator.

    Yields:
        Items from a random subset of the input iterator.

    Example:
        >>> list(reservoir_sampling(iter(range(100)), 10))
        [66, 83, 78, 56, 35, 39, 36, 72, 21, 79]
    """

    reservoir = []  # Initialize an empty iterator for the reservoir

    for i, item in enumerate(iterator):
        if i < n:
            reservoir.append(item)  # Fill the reservoir array with the first n items
        else:
            j = random.randint(0, i)

            if j < n:
                reservoir[j] = (
                    item  # Randomly replace elements in the reservoir with a decreasing probability.
                )

    for item in reservoir:
        yield item
