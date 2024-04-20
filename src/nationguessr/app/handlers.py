import logging

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart, ExceptionTypeFilter
from aiogram.fsm.context import FSMContext
from aiogram.types.bot_command import BotCommand
from aiogram.utils.markdown import bold

from ..data.game import GameSession
from ..service.fsm.state import BotState
from ..service.game import GuessingFactsGameService, record_new_score
from ..service.utils import batched
from ..settings import Settings

root_router = Router(name=__name__)
logger = logging.getLogger()


@root_router.error(ExceptionTypeFilter(Exception), F.update.message.as_("message"))
async def error_handler(event: types.ErrorEvent, message: types.Message):
    logger.critical(
        "Unhandled exception has occurred: %s", event.exception, exc_info=False
    )

    await message.answer(
        "⚠️ Oops, looks like we hit a snag! Please try again in a little bit."
    )


@root_router.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext) -> None:
    logger.info(
        f"User id={message.from_user.id} (chat_id={message.chat.id}) called a /start"
        " command"
    )

    await state.set_state(BotState.select_game)
    await message.answer(
        "🌍 Hey there, welcome to Nationguessr! I'm your friendly guide on this exciting journey around the globe,"
        " where you'll uncover fascinating facts about different countries. Think you can guess which country we're "
        "talking about from hints about its history, culture, geography, and loads more?\n\n🔄 Ready for a fresh start?"
        " Just type /restart and we'll dive into a new quiz adventure.\n🏆 Curious about your best scores? Hit /score "
        "to bask in your personal hall of fame.\n🧹 Want to start over and make new records? Use /clear to wipe the "
        "slate clean.\n\nSo, what do you say - ready to embark on a guessing game that takes you around the world? "
        "Let's get started!",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text="🔍 Guess from Facts"),
                    types.KeyboardButton(text="🚩 Guess by Flag"),
                ]
            ],
            resize_keyboard=True,
        ),
    )


@root_router.message(BotState.select_game, F.text == "🔍 Guess from Facts")
async def start_guess_facts_game(
    message: types.Message,
    state: FSMContext,
    facts_game_service: GuessingFactsGameService,
    app_settings: Settings,
) -> None:
    state_data = await state.get_data()
    game_round = await facts_game_service.new_game_round()

    new_game_session = GameSession(
        score_board=state_data.get("score_board", {}),
        lives_remained=app_settings.default_init_lives,
        current_score=0,
        options=game_round.options,
        correct_option=game_round.correct_option,
    )

    await state.set_state(BotState.playing_guess_facts)
    await state.update_data(**new_game_session.model_dump())
    await message.answer(
        f"🌟 Get ready for an exciting challenge! In this game, I'll share {app_settings.default_facts_num} intriguing "
        f"and unique facts about a mystery country. Your task? Guess the right country from "
        f"{app_settings.default_options_num} options - but there's only one correct answer!\n\nYou've got "
        f"{app_settings.default_init_lives}❤️ attempts to prove your skills. Aim high and see how high you can score! "
        f"Are you up for the challenge? Let's go! 🚀"
    )

    await message.answer(
        "\n".join([f"📍 {fact}" for fact in game_round.facts]),
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=option) for option in batch]
                for batch in batched(game_round.options, n=2)
            ],
            resize_keyboard=True,
        ),
    )


@root_router.message(BotState.playing_guess_facts, F.text.regexp(r"^[^/].*"))
async def play_guess_facts_game(
    message: types.Message,
    state: FSMContext,
    facts_game_service: GuessingFactsGameService,
) -> None:
    """The handler considers any user input as valid only if it is a bot command,
    i.e., it starts with a symbol '/', or an answer listed in the current game
    session options; otherwise, it treats the input as invalid.
    """

    state_data = await state.get_data()
    current_game_session = GameSession(**state_data)

    if message.text is None or message.text not in current_game_session.options:
        await message.answer(
            "🚀 Whoa there, trailblazer! Your answer was not on the list. Let's try again, shall we?"
        )
        current_game_session.lives_remained -= 1
    elif message.text != current_game_session.correct_option:
        await message.answer(
            f"😅 Almost nailed it! The right answer was '{current_game_session.correct_option}'. Ready to dive into "
            f"the next one?"
        )
        current_game_session.lives_remained -= 1
    else:
        await message.answer(
            "🎈 Phenomenal job! You've got it exactly right! Ready to dive into the next one?"
        )
        current_game_session.current_score += 1

    game_round = await facts_game_service.new_game_round()

    current_game_session.options = game_round.options
    current_game_session.correct_option = game_round.correct_option

    await state.update_data(**current_game_session.model_dump())
    await message.answer(
        "\n".join([f"📍 {fact}" for fact in game_round.facts]),
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=option) for option in batch]
                for batch in batched(game_round.options, n=2)
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

    state_data = await state.get_data()
    current_game_session = record_new_score(GameSession(**state_data))

    await state.update_data(**current_game_session.model_dump())
    await state.set_state(BotState.select_game)
    await message.answer(
        f"👾 {bold('GAME OVER')} 👾",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text="🔍 Guess from Facts"),
                    types.KeyboardButton(text="🚩 Guess by Flag"),
                ]
            ],
            resize_keyboard=True,
        ),
    )


@root_router.message(
    Command(BotCommand(command="score", description="View your top score in quiz"))
)
async def score_handler(message: types.Message, state: FSMContext) -> None:
    logger.info(
        f"User id={message.from_user.id} (chat_id={message.chat.id}) called a /score"
        " command"
    )

    state_data = await state.get_data()

    if state_data.get("score_board"):
        scores = GameSession(**state_data).score_board

        if len(scores) == 0:
            await message.answer("🌟 Your scoreboard is a blank canvas!")
        else:
            score_table = "\n".join(
                [
                    f"{i + 1}. {timestamp} - {score} point(s)"
                    for i, (timestamp, score) in enumerate(
                        sorted(scores.items(), key=lambda x: x[1], reverse=True)
                    )
                ]
            )

            await message.answer(
                f"*🏆 Top Scores 🏆*\n---\n{score_table}",
            )
    else:
        await message.answer("🌟 Your scoreboard is a blank canvas!")


@root_router.message(
    Command(BotCommand(command="clear", description="Clear your score table"))
)
async def clear_handler(message: types.Message, state: FSMContext) -> None:
    logger.info(
        f"User id={message.from_user.id} (chat_id={message.chat.id}) called a /clear"
        " command"
    )

    await state.clear()
    await message.answer(
        "🌟 The leaderboard's been wiped clean! Tap /start to jump into your next adventure! 🌟",
        reply_markup=types.ReplyKeyboardRemove(),
    )
