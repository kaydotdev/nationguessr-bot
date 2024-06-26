from itertools import islice
from random import randint
from typing import Generator, Iterable, List, TypeVar

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

    Raises:
        ValueError: If batch size is less than 1.

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


def reservoir_sampling(iterable: Iterable[T], n: int) -> List[T]:
    """Performs reservoir sampling over an iterator and returns another iterator
    yielding a random subset of n items from the input iterator. Sampling over
    the iterator allows us to work with big sets of data without allocating them
    into memory, for instance, using lists.

    Args:
        iterable (Iterable): The iterable to sample from.
        n (int): The desired sample size. Must be at least 1.

    Returns:
        List[T]: A list containing a randomly selected subset of n items from the input iterable.

    Raises:
        ValueError: If sample size is less than 1.

    Example:
        >>> reservoir_sampling(range(100), 10)
        [66, 83, 78, 56, 35, 39, 36, 72, 21, 79]

    Note:
        The output in the example is randomly generated each time the function is called,
        so the actual output may vary.
    """

    if n < 1:
        raise ValueError("Sample size must be at least 1")

    reservoir = []

    for index, item in enumerate(iterable):
        if index < n:
            reservoir.append(item)
        else:
            replace_index = randint(0, index)

            if replace_index < n:
                reservoir[replace_index] = item

    return reservoir
