import json
import random

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types.bot_command import BotCommand
from aiogram.utils.markdown import bold
from fsm import BotState
from models import GameSession
from models.facts import CountryCode, JSONReservoirSamplingGenerator
from utils import batched, validate_and_fetch_scores
from vars import DEFAULT_FACTS_NUM, DEFAULT_INIT_LIVES, DEFAULT_OPTIONS_NUM, TOP_SCORES

root_router = Router()


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
            keyboard=[
                [
                    types.KeyboardButton(text="Guess from facts"),
                    types.KeyboardButton(text="Guess by flag"),
                ]
            ],
            resize_keyboard=True,
        ),
    )


@root_router.message(BotState.select_game, F.text == "Guess from facts")
async def start_guess_facts_game(message: types.Message, state: FSMContext) -> None:
    with open("./data/dev/names.json") as f:
        country_names = json.load(f)

    selected_country_codes = random.sample(country_names.keys(), DEFAULT_OPTIONS_NUM)
    selected_correct_code = random.choice(selected_country_codes)

    facts_generator = JSONReservoirSamplingGenerator(
        "./data/dev/facts.json",
        CountryCode(code=selected_correct_code),
        DEFAULT_FACTS_NUM
    )

    options = [country_names.get(code) for code in selected_country_codes]
    correct_option = country_names.get(selected_correct_code)

    new_game_session = GameSession(
        lives_remained=DEFAULT_INIT_LIVES,
        current_score=0,
        options=options,
        correct_option=correct_option,
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
        "\n".join([f"📍 {fact}" for fact in facts_generator.generate()]),
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=option) for option in batch]
                for batch in batched(options, n=2)
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
        score_table = "\n".join([
            f"{bold(timestamp)}: {score}" for timestamp, score in scores.items()
        ])
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
