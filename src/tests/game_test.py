import pytest
from nationguessr.data.game import GameSession
from nationguessr.service.game import number_as_character, record_new_score
from nationguessr.settings import Settings


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


class TestRecordNewScore:
    @pytest.fixture(autouse=True)
    def _default_app_settings(self):
        self._settings = Settings(
            default_top_scores=5,
            token="",
            aws_access_key="",
            aws_secret_key="",
            aws_fsm_table_name="",
            aws_region="",
        )

    @pytest.fixture(autouse=True)
    def _default_game_session(self):
        self._current_game_session = GameSession(
            score_board={},
            lives_remained=5,
            current_score=0,
            options=[],
            correct_option="",
        )

    def test_should_reset_current_score_and_update_the_table(self):
        # arrange
        self._current_game_session.current_score = 69

        expected_recorded_scores = [69]

        # act
        new_game_session = record_new_score(self._current_game_session, self._settings)

        # assert
        assert new_game_session.current_score == 0
        assert list(new_game_session.score_board.keys()) == expected_recorded_scores

    def test_should_discard_new_score_if_all_top_scores_are_greater(self):
        # arrange
        self._current_game_session.current_score = 69
        self._current_game_session.score_board = {
            2048: "01/01/1970",
            1024: "01/01/1970",
            512: "01/01/1970",
            256: "01/01/1970",
            128: "01/01/1970",
        }

        expected_recorded_scores = [2048, 1024, 512, 256, 128]

        # act
        new_game_session = record_new_score(self._current_game_session, self._settings)

        # assert
        assert list(new_game_session.score_board.keys()) == expected_recorded_scores

    def test_should_update_score_with_similar_value_in_the_table(self):
        # arrange
        current_score = 69

        self._current_game_session.current_score = current_score
        self._current_game_session.score_board = {
            2048: "01/01/1970",
            1024: "01/01/1970",
            512: "01/01/1970",
            256: "01/01/1970",
            69: "01/01/1970",
        }

        expected_recorded_scores = [2048, 1024, 512, 256, 69]

        # act
        new_game_session = record_new_score(self._current_game_session, self._settings)

        # assert
        # I couldn't find the proper way to mock `datetime.datetime.utcnow()` since it's a built-in type,
        # so instead I just check whether the timestamp value has changed from the default.
        assert new_game_session.score_board[current_score] != "01/01/1970"
        assert list(new_game_session.score_board.keys()) == expected_recorded_scores

    def test_should_update_score_table_if_current_score_greater_than_min_recorded_score(
        self,
    ):
        # arrange
        current_score = 69

        self._current_game_session.current_score = current_score
        self._current_game_session.score_board = {
            64: "01/01/1970",
            256: "01/01/1970",
            128: "01/01/1970",
            32: "01/01/1970",
            512: "01/01/1970",
        }

        expected_recorded_scores = [64, 256, 128, 512, 69]

        # act
        new_game_session = record_new_score(self._current_game_session, self._settings)

        # assert
        assert list(new_game_session.score_board.keys()) == expected_recorded_scores
