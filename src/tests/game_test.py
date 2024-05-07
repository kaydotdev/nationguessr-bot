import pytest
from nationguessr.service.game import number_as_character


class TestNumberAsCharacter:
    def test_should_raise_value_error_if_input_integer_is_negative(self):
        with pytest.raises(ValueError):
            number_as_character(-1)

    def test_should_raise_value_error_if_number_of_slots_is_less_than_one(self):
        with pytest.raises(ValueError):
            number_as_character(1, slots=0)

    def test_should_raise_value_error_if_char_map_is_invalid(self):
        with pytest.raises(ValueError):
            number_as_character(1, slots=1, char_map=[])

    def test_should_convert_to_string_if_input_is_zero_with_custom_slots(self):
        # arrange
        expected_string = "000000"

        # act
        actual_string = number_as_character(0, slots=6)

        # assert
        assert expected_string == actual_string

    def test_should_left_pad_zeros_if_slots_number_greater_than_digits(self):
        # arrange
        expected_string = "00045036"

        # act
        actual_string = number_as_character(45036, slots=8)

        # assert
        assert expected_string == actual_string

    def test_should_convert_to_string_if_slots_number_less_than_digits(self):
        # arrange
        expected_string = "45036"

        # act
        actual_string = number_as_character(45036, slots=1)

        # assert
        assert expected_string == actual_string

    def test_should_convert_to_string_with_custom_digit_map(self):
        # arrange
        custom_map = ["9", "8", "7", "6", "5", "4", "3", "2", "1", "0"]
        expected_string = "54"

        # act
        actual_string = number_as_character(45, slots=1, char_map=custom_map)

        # assert
        assert expected_string == actual_string

    def test_should_convert_to_string_with_emoji_digit_map(self):
        # arrange
        custom_map = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
        expected_string = "4️⃣5️⃣"

        # act
        actual_string = number_as_character(45, slots=1, char_map=custom_map)

        # assert
        assert expected_string == actual_string
