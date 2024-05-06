import pytest
from nationguessr.service.utils import batched, reservoir_sampling


class TestBatched:
    def test_should_raise_value_error_if_batch_size_less_than_one(self):
        with pytest.raises(ValueError):
            list(batched([0], 0))

    def test_should_generate_batches_if_iterator_is_empty(self):
        # arrange
        expected_batches = []

        # act
        actual_batches = list(batched([], 2))

        # assert
        assert expected_batches == actual_batches

    def test_should_generate_batches_with_single_element(self):
        # arrange
        expected_batches = [(1,), (2,), (3,)]

        # act
        actual_batches = list(batched([1, 2, 3], 1))

        # assert
        assert expected_batches == actual_batches

    def test_should_generate_batches_with_even_element_distribution(self):
        # arrange
        expected_batches = [(0, 1, 2), (3, 4, 5)]

        # act
        actual_batches = list(batched(range(6), 3))

        # assert
        assert expected_batches == actual_batches

    def test_should_generate_batches_with_uneven_element_distribution(self):
        # arrange
        expected_batches = [(0, 1, 2), (3, 4, 5), (6,)]

        # act
        actual_batches = list(batched(range(7), 3))

        # assert
        assert expected_batches == actual_batches


class TestReservoirSampling:
    def test_should_raise_value_error_if_sample_size_less_than_one(self):
        with pytest.raises(ValueError):
            reservoir_sampling(range(1), 0)

    def test_should_sample_from_empty_reservoir(self):
        # arrange
        expected_samples = []

        # act
        actual_samples = reservoir_sampling([], 1)

        # assert
        assert expected_samples == actual_samples

    def test_should_sample_hashable_reservoir(self, mocker):
        # arrange
        mock_randint = mocker.patch("nationguessr.service.utils.randint")
        mock_randint.side_effect = [8, 5, 4, 7, 6, 9, 2, 3]

        expected_samples = [0, 1, 9]

        # act
        actual_samples = reservoir_sampling(range(10), 3)

        # assert
        assert expected_samples == actual_samples

    def test_should_sample_non_hashable_reservoir(self, mocker):
        # arrange
        mock_randint = mocker.patch("nationguessr.service.utils.randint")
        mock_randint.side_effect = [2, 3, 1]

        expected_samples = [{"a": 0}]

        # act
        actual_samples = reservoir_sampling([{"a": 0}, {"b": 1}, {"c": 2}], 1)

        # assert
        assert expected_samples == actual_samples
