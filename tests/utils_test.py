from datetime import datetime
from unittest.mock import AsyncMock
from pydantic import ValidationError

import pytest

from src.utils import validate_and_fetch_scores

pytest_plugins = ("pytest_asyncio",)


def build_mock(param):
    mock = AsyncMock()
    mock.get_data.return_value = param

    return mock


@pytest.fixture(scope="function", params=[{}, {"score": None}])
def empty_fsm_mock(request):
    return build_mock(request.param)


@pytest.fixture(
    scope="function",
    params=[
        {
            "scores": {
                datetime(year=1970, month=1, day=1): 10,
                datetime(year=1971, month=1, day=1): 0,
            }
        }
    ],
)
def non_empty_fsm_mock(request):
    return build_mock(request.param), request.param


@pytest.fixture(
    scope="function",
    params=[
        {
            "scores": {
                datetime(year=1970, month=1, day=1): "",
            }
        },
        {
            "scores": {
                datetime(year=1970, month=1, day=1): -1,
            }
        },
        {
            "scores": {
                "": 10,
            }
        }
    ],
)
def corrupted_fsm_mock(request):
    return build_mock(request.param)


@pytest.mark.asyncio
async def test_validate_and_fetch_scores_should_return_empty_state(empty_fsm_mock):
    # act
    state = await validate_and_fetch_scores(empty_fsm_mock)

    # assert
    empty_fsm_mock.get_data.assert_called_once()
    assert state.records == {}


@pytest.mark.asyncio
async def test_validate_and_fetch_scores_should_return_recorded_state_from_fsm(
    non_empty_fsm_mock,
):
    # arrange
    fsm, data = non_empty_fsm_mock

    # act
    state = await validate_and_fetch_scores(fsm)

    # assert
    fsm.get_data.assert_called_once()
    assert state.records == data["scores"]


@pytest.mark.asyncio
async def test_validate_and_fetch_scores_should_throw_if_fsm_state_is_corrupted(
    corrupted_fsm_mock,
):
    with pytest.raises(ValidationError):
        _ = await validate_and_fetch_scores(corrupted_fsm_mock)
