import io
import logging
import os

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart, ExceptionTypeFilter
from aiogram.fsm.context import FSMContext
from aiogram.types.bot_command import BotCommand
from PIL import Image

from ..data.game import GameSession
from ..service.fsm.state import BotState
from ..service.game import GuessingFactsGameService, draw_game_bar, record_new_score
from ..service.image import ImageEditService
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
        "🌍 Hello and welcome to Nationguessr! I'm here to guide you through an enthralling journey across "
        "continents as we explore incredible facts about different countries. Ready to test your knowledge and "
        "guess which nation we’re hinting at from snippets about its history, culture, and geography?\n\n🔄 Feel "
        "like starting fresh? Just type /restart and we’ll kick off another exciting quiz adventure.\n🏆 Want to "
        "relive your victories? Hit /score to revel in your personal hall of fame.\n🧹 Ready to reset and break "
        "new records? Use /clear to wipe the slate clean.\n📚 Need a quick guide on how to play? Tap /tutorial "
        "for a brief overview of our quiz games.\n\nSo, what do you think—eager to start a guessing game that "
        "transports you around the world? Let’s jump right in!",
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
    text_on_image_service: ImageEditService,
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

    quiz_card_template_path = os.path.join(
        app_settings.assets_folder, "cards", "game_guessing.png"
    )

    with (
        Image.open(quiz_card_template_path) as quiz_card_template,
        io.BytesIO() as img_buffer,
    ):
        numerated_text = [
            f"{i + 1}. {chunk}" for i, chunk in enumerate(game_round.facts)
        ]
        quiz_card_image = text_on_image_service.add_multiline_text(
            quiz_card_template, numerated_text, position=(0, -100), center=True
        )
        quiz_card_image.save(img_buffer, format="PNG")

        img_buffer.seek(0)

        await message.answer_photo(
            types.BufferedInputFile(img_buffer.read(), filename="quiz_card.png"),
            caption=draw_game_bar(new_game_session, app_settings)
            + "\n\nGet ready for an exciting challenge! Here are "
            "5 intriguing facts about the country. Do you know "
            "the right answer?",
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
    text_on_image_service: ImageEditService,
    score_edit_service: ImageEditService,
    app_settings: Settings,
) -> None:
    """The handler considers any user input as valid only if it is a bot command,
    i.e., it starts with a symbol '/', or an answer listed in the current game
    session options; otherwise, it treats the input as invalid.
    """

    state_data = await state.get_data()
    current_game_session = GameSession(**state_data)

    if message.text is None or message.text not in current_game_session.options:
        response_message = "🚀 Whoa there, trailblazer! Your answer was not on the list. Let's try again, shall we?"
        current_game_session.lives_remained -= 1
    elif message.text != current_game_session.correct_option:
        response_message = (
            f"😅 Almost nailed it! The right answer was '{current_game_session.correct_option}'. Ready "
            f"to dive into the next one?"
        )
        current_game_session.lives_remained -= 1
    else:
        response_message = "🌟 Phenomenal job! You've got it exactly right! Ready to dive into the next one?"
        current_game_session.current_score += 1

    if current_game_session.lives_remained == 0:
        await end_game_and_display_score(
            message, state, current_game_session, score_edit_service, app_settings
        )

        return

    game_round = await facts_game_service.new_game_round()

    current_game_session.options = game_round.options
    current_game_session.correct_option = game_round.correct_option

    await state.update_data(**current_game_session.model_dump())

    quiz_card_template_path = os.path.join(
        app_settings.assets_folder, "cards", "game_guessing.png"
    )

    with (
        Image.open(quiz_card_template_path) as quiz_card_template,
        io.BytesIO() as img_buffer,
    ):
        numerated_text = [
            f"{i + 1}. {chunk}" for i, chunk in enumerate(game_round.facts)
        ]
        quiz_card_image = text_on_image_service.add_multiline_text(
            quiz_card_template, numerated_text, position=(0, -100), center=True
        )
        quiz_card_image.save(img_buffer, format="PNG")

        img_buffer.seek(0)

        await message.answer_photo(
            types.BufferedInputFile(img_buffer.read(), filename="quiz_card.png"),
            caption=draw_game_bar(current_game_session, app_settings)
            + "\n\n"
            + response_message,
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
async def restart_handler(
    message: types.Message,
    state: FSMContext,
    score_edit_service: ImageEditService,
    app_settings: Settings,
) -> None:
    logger.info(
        f"User id={message.from_user.id} (chat_id={message.chat.id}) called a /restart"
        " command"
    )

    state_data = await state.get_data()
    current_game_session = GameSession(**state_data)
    await end_game_and_display_score(
        message, state, current_game_session, score_edit_service, app_settings
    )


@root_router.message(
    Command(
        BotCommand(
            command="tutorial", description="A brief description about quiz games"
        )
    )
)
async def tutorial_handler(message: types.Message, app_settings: Settings) -> None:
    logger.info(
        f"User id={message.from_user.id} (chat_id={message.chat.id}) called a /tutorial command"
    )

    await message.answer(
        "🌍 Get ready to embark on an exhilarating journey with our 'Guess from Facts' and 'Guess by Flag' games!\n\n"
        f"🔍 In 'Guess from Facts', I'll select a random country and reveal {app_settings.default_facts_num} intriguing"
        f" facts about it. You'll see {app_settings.default_options_num} options, but only one is correct. Can you "
        f"pinpoint the right country on each turn? Be cautious — you're only allowed {app_settings.default_init_lives}"
        " mistakes per game, after which it's game over!\n\n🚩 In 'Guess by Flag', I'll show you the flag of a mystery "
        "country alongside 4 possible choices. Your challenge is to correctly identify the country's flag with each "
        "attempt.\n\nAre you thrilled to dive in and start playing? Let’s see how much you know about the world! 🌐"
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
                    for i, (score, timestamp) in enumerate(
                        sorted(scores.items(), key=lambda x: x[0], reverse=True)
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


async def end_game_and_display_score(
    message: types.Message,
    state: FSMContext,
    game_session: GameSession,
    score_edit_service: ImageEditService,
    app_settings: Settings,
) -> None:
    current_score = game_session.current_score
    current_game_session = record_new_score(game_session, app_settings)

    game_over_card_template_path = os.path.join(
        app_settings.assets_folder, "cards", "game_over.png"
    )

    with (
        Image.open(game_over_card_template_path) as game_over_card_template,
        io.BytesIO() as img_buffer,
    ):
        game_over_card_image = score_edit_service.add_text(
            game_over_card_template,
            str(current_score),
            position=(0, 10),
            center=True,
        )
        game_over_card_image.save(img_buffer, format="PNG")

        img_buffer.seek(0)

        await state.set_state(BotState.select_game)
        await state.update_data(**current_game_session.model_dump())
        await message.answer_photo(
            types.BufferedInputFile(img_buffer.read(), filename="game_over_card.png"),
            caption="👾 The game is over! Want to give it another go? Just select new game from the options below to "
                    "start fresh!",
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
