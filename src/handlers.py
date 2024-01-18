import json
import logging
import random

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types.bot_command import BotCommand
from aiogram.utils.markdown import bold
from fsm import BotState
from models import CountryCode, json_fetch_country_facts
from state import GameSession
from utils import batched, reservoir_sampling, validate_and_fetch_scores
from vars import (
    COUNTRY_FACTS_FILE_LOCATION,
    COUNTRY_NAMES_FILE_LOCATION,
    DEFAULT_FACTS_NUM,
    DEFAULT_INIT_LIVES,
    DEFAULT_OPTIONS_NUM,
    TOP_SCORES,
)

root_router = Router()
logger = logging.getLogger()


def guess_facts_round():
    with (
        open(COUNTRY_FACTS_FILE_LOCATION) as country_facts_file,
        open(COUNTRY_NAMES_FILE_LOCATION) as country_names_file,
    ):
        country_names = json.load(country_names_file)

        selected_country_codes = random.sample(
            country_names.keys(), DEFAULT_OPTIONS_NUM
        )
        selected_correct_code = random.choice(selected_country_codes)
        selected_country_facts = [
            f"📍 {fact}"
            for fact in reservoir_sampling(
                json_fetch_country_facts(
                    country_facts_file, CountryCode(code=selected_correct_code)
                ),
                DEFAULT_FACTS_NUM,
            )
        ]

    country_options = [country_names.get(code) for code in selected_country_codes]
    country_correct_option = country_names.get(selected_correct_code)

    return selected_country_facts, country_options, country_correct_option


@root_router.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext) -> None:
    await state.set_state(BotState.select_game)
    await message.answer(
        "🌎 Hi there, I'm Nationguessr! With me, you get to test your knowledge"
        " about countries from all over the world by trying to guess them based on"
        " random facts about their history, culture, geography, and much"
        " more!\n\n🔁 To play a quiz from the beginning use the /restart"
        " command.\n🔝 To see your highest score in the quiz use the /score"
        " command.\n🆑 To clear all your high score history use the /clear"
        " command.\n\nNow, let's see - which game would you like to play?",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[
                types.KeyboardButton(text="Guess from facts"),
                types.KeyboardButton(text="Guess by flag"),
            ]],
            resize_keyboard=True,
        ),
    )


@root_router.message(BotState.select_game, F.text == "Guess from facts")
async def start_guess_facts_game(message: types.Message, state: FSMContext) -> None:
    try:
        selected_country_facts, country_options, country_correct_option = (
            guess_facts_round()
        )
    except (FileNotFoundError, PermissionError, IsADirectoryError) as ex:
        logger.error(f"Failed to open files with country names and facts: {ex}")
        return

    new_game_session = GameSession(
        lives_remained=DEFAULT_INIT_LIVES,
        current_score=0,
        options=country_options,
        correct_option=country_correct_option,
    )

    await state.set_state(BotState.playing_guess_facts)
    await state.update_data(**new_game_session.model_dump())
    await message.answer(
        "🌟 Get ready for an exciting challenge! In this game, I'll share"
        f" {DEFAULT_FACTS_NUM} intriguing and unique facts about a mystery country."
        f" Your task? Guess the right country from {DEFAULT_OPTIONS_NUM} options - but"
        f" there's only one correct answer!\n\nYou've got {DEFAULT_INIT_LIVES}❤️"
        " attempts to prove your skills. Aim high and see how high you can score! Are"
        " you up for the challenge? Let's go! 🚀"
    )

    await message.answer(
        "\n".join(selected_country_facts),
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=option) for option in batch]
                for batch in batched(country_options, n=2)
            ],
            resize_keyboard=True,
        ),
    )


@root_router.message(BotState.playing_guess_facts, F.text.regexp(r"^[^/].*"))
async def play_guess_facts_game(message: types.Message, state: FSMContext) -> None:
    """The handler considers any user input as valid only if it is a bot command,
    i.e., it starts with a symbol '/', or an answer listed in the current game
    session options; otherwise, it treats the input as invalid.
    """

    state_data = await state.get_data()
    current_game_session = GameSession(**state_data)

    if message.text is None or message.text not in current_game_session.options:
        await message.answer(
            "🤔 Oops! Looks like there was a mix-up with the entry. Remember, the trick"
            " is to pick one of the options below. No worries, though! Let's tackle the"
            " next question and keep the fun rolling. Onwards and upwards!"
        )
        current_game_session.lives_remained -= 1
    elif message.text != current_game_session.correct_option:
        await message.answer(
            "😰 Oops, close but not quite! The correct answer was"
            f" '{current_game_session.correct_option}'. Let's keep the energy up and"
            " dive into the next question - you've got this!"
        )
        current_game_session.lives_remained -= 1
    else:
        await message.answer(
            "🌟 Absolutely brilliant! You nailed it! 🎉 Get ready to keep the streak "
            "going with this next one – your next challenge awaits!"
        )
        current_game_session.current_score += 1

    try:
        selected_country_facts, country_options, country_correct_option = (
            guess_facts_round()
        )
    except (FileNotFoundError, PermissionError, IsADirectoryError) as ex:
        logger.error(f"Failed to open files with country names and facts: {ex}")
        return

    current_game_session.options = country_options
    current_game_session.correct_option = country_correct_option

    await state.update_data(**current_game_session.model_dump())
    await message.answer(
        "\n".join(selected_country_facts),
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=option) for option in batch]
                for batch in batched(country_options, n=2)
            ],
            resize_keyboard=True,
        ),
    )


@root_router.message(
    Command(
        BotCommand(
            command="restart", description="Start your quiz from the very beginning"
        )
    )
)
async def restart_handler(message: types.Message, state: FSMContext) -> None:
    await state.set_state(state=None)
    await message.answer("TODO: Restart command.")


@root_router.message(
    Command(BotCommand(command="score", description="View your top score in quiz"))
)
async def score_handler(message: types.Message, state: FSMContext) -> None:
    scores = await validate_and_fetch_scores(state)

    if len(scores.records) == 0:
        await message.answer(
            "🌟 Your scoreboard is a blank canvas waiting to be filled with your"
            " achievements! Dive into some games and start racking up those scores."
            " Each game you play adds a new high score to your list. How high can you"
            " go? Let the games begin! 🚀"
        )
    else:
        score_table = "\n".join(
            [f"{bold(timestamp)}: {score}" for timestamp, score in scores.items()]
        )
        await message.answer(
            f"🌟 Wow! You've been on a roll! Check out your top {TOP_SCORES} scores"
            " shining on the leaderboard! Keep up the great work - can you beat your"
            f" own records? 🚀\n\n{score_table}"
        )


@root_router.message(
    Command(BotCommand(command="clear", description="Clear your score table"))
)
async def clear_handler(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🎉 All clear! Your high score board is now a clean slate, ready for new"
        " victories. Hit the /start command to dive into a new game and set some"
        " impressive new records!",
        reply_markup=types.ReplyKeyboardRemove(),
    )
