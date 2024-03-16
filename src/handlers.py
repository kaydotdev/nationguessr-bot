import logging
import random
import sqlite3

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types.bot_command import BotCommand
from aiogram.utils.markdown import bold
from fsm import BotState
from models import GameSession, ScoreBoard
from utils import (
    batched,
    select_bot_replica,
    select_random_country_facts,
    select_random_country_options,
)
from vars import (
    DEFAULT_FACTS_NUM,
    DEFAULT_INIT_LIVES,
    DEFAULT_OPTIONS_NUM,
    TOP_SCORES,
)

root_router = Router(name=__name__)
logger = logging.getLogger()


@root_router.message(CommandStart())
async def start_handler(
    message: types.Message, state: FSMContext, db_connection: sqlite3.Connection
) -> None:
    logger.info(
        f"User id={message.from_user.id} (chat_id={message.chat.id}) called a /start"
        " command"
    )

    cursor = db_connection.cursor()
    intro_replica = select_bot_replica(cursor, "INTRO").replica

    await state.set_state(BotState.select_game)
    await message.answer(
        intro_replica,
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[
                types.KeyboardButton(text="🔍 Guess from Facts"),
                types.KeyboardButton(text="🚩 Guess by Flag"),
            ]],
            resize_keyboard=True,
        ),
    )


@root_router.message(BotState.select_game, F.text == "🔍 Guess from Facts")
async def start_guess_facts_game(
    message: types.Message, state: FSMContext, db_connection: sqlite3.Connection
) -> None:
    cursor = db_connection.cursor()
    country_options = [
        country.name
        for country in select_random_country_options(cursor, DEFAULT_OPTIONS_NUM)
    ]
    country_correct_option = random.choice(country_options)
    selected_country_facts = select_random_country_facts(
        cursor, country_correct_option, DEFAULT_FACTS_NUM
    )

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
        "\n".join([f"📍 {fact.content}" for fact in selected_country_facts]),
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=option) for option in batch]
                for batch in batched(country_options, n=2)
            ],
            resize_keyboard=True,
        ),
    )


@root_router.message(BotState.playing_guess_facts, F.text.regexp(r"^[^/].*"))
async def play_guess_facts_game(
    message: types.Message, state: FSMContext, db_connection: sqlite3.Connection
) -> None:
    """The handler considers any user input as valid only if it is a bot command,
    i.e., it starts with a symbol '/', or an answer listed in the current game
    session options; otherwise, it treats the input as invalid.
    """

    state_data = await state.get_data()
    current_game_session = GameSession(**state_data)
    cursor = db_connection.cursor()

    if message.text is None or message.text not in current_game_session.options:
        unavailable_option_replica = select_bot_replica(
            cursor, "GAME_ROUND_NOT_IN_OPTIONS"
        ).replica
        await message.answer(unavailable_option_replica)
        current_game_session.lives_remained -= 1
    elif message.text != current_game_session.correct_option:
        wrong_answer_replica = select_bot_replica(
            cursor, "GAME_ROUND_WRONG_ANSWER"
        ).replica
        await message.answer(
            wrong_answer_replica.format(current_game_session.correct_option)
        )
        current_game_session.lives_remained -= 1
    else:
        correct_answer_replica = select_bot_replica(
            cursor, "GAME_ROUND_CORRECT_ANSWER"
        ).replica
        await message.answer(correct_answer_replica)
        current_game_session.current_score += 1

    country_options = [
        country.name
        for country in select_random_country_options(cursor, DEFAULT_OPTIONS_NUM)
    ]
    country_correct_option = random.choice(country_options)
    selected_country_facts = select_random_country_facts(
        cursor, country_correct_option, DEFAULT_FACTS_NUM
    )

    current_game_session.options = country_options
    current_game_session.correct_option = country_correct_option

    await state.update_data(**current_game_session.model_dump())
    await message.answer(
        "\n".join([f"📍 {fact.content}" for fact in selected_country_facts]),
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
            command="restart",
            description="End current game and return to the selection menu",
        )
    )
)
async def restart_handler(message: types.Message, state: FSMContext) -> None:
    logger.info(
        f"User id={message.from_user.id} (chat_id={message.chat.id}) called a /restart"
        " command"
    )

    await state.set_state(BotState.select_game)
    await message.answer(
        "🎉 All clear! Your high score board is now a clean slate, ready for new"
        " victories. Hit the /start command to dive into a new game and set some"
        " impressive new records!",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[
                types.KeyboardButton(text="🔍 Guess from Facts"),
                types.KeyboardButton(text="🚩 Guess by Flag"),
            ]],
            resize_keyboard=True,
        ),
    )


@root_router.message(
    Command(BotCommand(command="score", description="View your top score in quiz"))
)
async def score_handler(
    message: types.Message, state: FSMContext, db_connection: sqlite3.Connection
) -> None:
    logger.info(
        f"User id={message.from_user.id} (chat_id={message.chat.id}) called a /score"
        " command"
    )

    state_data = await state.get_data()
    score_data = state_data.get("scores", {})
    scores = ScoreBoard(records=score_data)
    cursor = db_connection.cursor()

    if len(scores.records) == 0:
        await message.answer(
            "🌟 Your scoreboard is a blank canvas waiting to be filled with your"
            " achievements! Dive into some games and start racking up those scores."
            " Each game you play adds a new high score to your list. How high can"
            " you go? Let the games begin! 🚀",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    else:
        show_scoreboard_replica = select_bot_replica(cursor, "SHOW_SCOREBOARD").replica
        score_table = "\n".join([
            f"{bold(timestamp.strftime('%m/%d/%Y, %H:%M:%S'))}: {score}"
            for timestamp, score in scores.records.items()
        ])
        await message.answer(
            show_scoreboard_replica.format(TOP_SCORES, score_table),
            reply_markup=types.ReplyKeyboardRemove(),
        )


@root_router.message(
    Command(BotCommand(command="clear", description="Clear your score table"))
)
async def clear_handler(
    message: types.Message, state: FSMContext, db_connection: sqlite3.Connection
) -> None:
    logger.info(
        f"User id={message.from_user.id} (chat_id={message.chat.id}) called a /clear"
        " command"
    )

    cursor = db_connection.cursor()
    clear_replica = select_bot_replica(cursor, "CLEAR_SCORES").replica

    await state.clear()
    await message.answer(clear_replica, reply_markup=types.ReplyKeyboardRemove())
