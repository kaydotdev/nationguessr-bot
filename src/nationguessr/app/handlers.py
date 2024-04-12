import logging

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types.bot_command import BotCommand
from aiogram.utils.markdown import bold

from ..data.game import GameSession, ScoreBoard
from ..service.fsm.state import BotState
from ..service.game import GuessingFactsGameService
from ..service.utils import batched
from ..settings import Settings

root_router = Router(name=__name__)
logger = logging.getLogger()


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
    game_round = await facts_game_service.new_game_round()

    new_game_session = GameSession(
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
            "🚀 Whoa there, trailblazer! You went for a choice that's outside our little box of "
            "options. It's all good – think of it as taking the scenic route. Ready to jump back "
            "on track? The next question is ready for your expert guessing!"
        )
        current_game_session.lives_remained -= 1
    elif message.text != current_game_session.correct_option:
        await message.answer(
            f"😅 Almost nailed it! The right answer was '{current_game_session.correct_option}'. "
            "No worries, though! Let's shake that off and charge into the next question with full "
            "steam. You're doing great - I believe in you!"
        )
        current_game_session.lives_remained -= 1
    else:
        await message.answer(
            "🎈 Phenomenal job! You've got it exactly right! Ready to dive into the next one? Let's "
            "see if you can keep this amazing run going. Onward to the next question!"
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

    await state.set_state(BotState.select_game)
    await message.answer(
        "🎉 All clear! Your high score board is now a clean slate, ready for new"
        " victories. Hit the /start command to dive into a new game and set some"
        " impressive new records!",
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
async def score_handler(
    message: types.Message, state: FSMContext, app_settings: Settings
) -> None:
    logger.info(
        f"User id={message.from_user.id} (chat_id={message.chat.id}) called a /score"
        " command"
    )

    state_data = await state.get_data()
    score_data = state_data.get("scores", {})
    scores = ScoreBoard(records=score_data)

    if len(scores.records) == 0:
        await message.answer(
            "🌟 Your scoreboard is a blank canvas waiting to be filled with your"
            " achievements! Dive into some games and start racking up those scores."
            " Each game you play adds a new high score to your list. How high can"
            " you go? Let the games begin! 🚀",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    else:
        score_table = "\n".join(
            [
                f"{bold(timestamp.strftime('%m/%d/%Y, %H:%M:%S'))}: {score}"
                for timestamp, score in scores.records.items()
            ]
        )
        await message.answer(
            f"🌟 Look at that! Your top {app_settings.default_top_scores} scores are sparkling at the top of the "
            "leaderboard like stars in the night sky! Keep this incredible momentum going. Can you surpass your own "
            f"achievements? It's time to break your own records!\n\n{score_table}",
            reply_markup=types.ReplyKeyboardRemove(),
        )


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
        "The leaderboard's been wiped clean, it's a fresh start! 🌈 Tap /start to jump into "
        "your next adventure and carve out your spot at the top. Let's see those high scores soar! 🌟",
        reply_markup=types.ReplyKeyboardRemove(),
    )
