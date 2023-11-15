import asyncio
import logging
import os
import json

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types.bot_command import BotCommand
from aiogram.utils.markdown import bold

from fsm import BotState
from models import ScoreBoard, GameSession


TOP_SCORES = 10
DEFAULT_INIT_LIVES = 5

logger = logging.getLogger()
logger.setLevel(logging.INFO)


TOKEN = os.getenv("BOT_TOKEN") or ""
root_router = Router()


async def validate_and_fetch_scores(state: FSMContext) -> ScoreBoard:
    state_data = await state.get_data()
    score_data = state_data.get("scores", {})

    return ScoreBoard(records=score_data)


@root_router.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext) -> None:
    await state.set_state(BotState.select_game)
    await message.answer(
        "🌎 Hi there, I'm Nationguessr! With me, you get to test your knowledge about countries from all over "
        "the world by trying to guess them based on random facts about their history, culture, geography, and "
        "much more!\n\n🔁 To play a quiz from the beginning use the /restart command.\n"
        "🔝 To see your highest score in the quiz use the /score command.\n"
        "🆑 To clear all your high score history use the /clear command.\n\n"
        "Now, let's see - which game would you like to play?",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text="Guess from facts"),
                    types.KeyboardButton(text="Guess by flag")
                ]
            ],
            resize_keyboard=True
        )
    )


@root_router.message(BotState.select_game, F.text == "Guess from facts")
async def start_guess_facts_game(message: types.Message, state: FSMContext) -> None:
    new_game_session = GameSession(lives_remained=DEFAULT_INIT_LIVES, current_score=0,
                                   options=["Country 1", "Country 2", "Country 3", "Country 4"],
                                   correct_option="Country 1")

    await state.set_state(BotState.playing_guess_facts)
    await state.update_data(**new_game_session.model_dump())
    await message.answer(
        f"🌟 Ready for an adventure around the globe? In this thrilling game, you'll receive five tantalizing clues "
        f"about a mysterious country. Your mission? Sift through four options to uncover the correct one! But choose "
        f"wisely – you only have five shots at glory. Rack up your score and aim for the top. Can you master the "
        f"challenge and become a geography genius? Let the guessing begin! 🌟"
    )


@root_router.message(Command(BotCommand(command="restart", description="Start your quiz from the very beginning")))
async def restart_handler(message: types.Message, state: FSMContext) -> None:
    await state.set_state(state=None)
    await message.answer("TODO: Restart command.")


@root_router.message(Command(BotCommand(command="score", description="View your top score in quiz")))
async def score_handler(message: types.Message, state: FSMContext) -> None:
    scores = await validate_and_fetch_scores(state)

    if len(scores.records) == 0:
        await message.answer(
            "🌟 Your scoreboard is a blank canvas waiting to be filled with your achievements! Dive into some games "
            "and start racking up those scores. Each game you play adds a new high score to your list. "
            "How high can you go? Let the games begin! 🚀"
        )
    else:
        score_table = "\n".join([f"{bold(timestamp)}: {score}" for timestamp, score in scores.items()])
        await message.answer(
            f"🌟 Wow! You've been on a roll! "
            f"Check out your top {TOP_SCORES} scores shining on the leaderboard! "
            f"Keep up the great work - can you beat your own records? 🚀\n\n{score_table}"
        )


@root_router.message(Command(BotCommand(command="clear", description="Clear your score table")))
async def clear_handler(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🎉 All clear! Your high score board is now a clean slate, ready for new victories. "
        "Hit the /start command to dive into a new game and set some impressive new records!",
        reply_markup=types.ReplyKeyboardRemove()
    )


async def main(update_event) -> None:
    update_obj = types.Update(**update_event)

    bot = Bot(TOKEN, parse_mode=ParseMode.MARKDOWN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(root_router)

    await dp.feed_update(bot=bot, update=update_obj)


def handler(event, context):
    update_event = json.loads(event.get('body', '{}'))
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main(update_event))
    except Exception as ex:
        logger.error(f"Error while executing lambda: '{ex}'")
        return {'statusCode': 500}

    return {'statusCode': 204}
