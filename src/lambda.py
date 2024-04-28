import asyncio
import json
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from nationguessr.app.handlers import root_router
from nationguessr.service.fsm.storage import DynamoDBStorage
from nationguessr.service.game import (
    GenerationFromGptStrategy,
    GenerationFromZipStrategy,
    GuessingFactsGameService,
)
from nationguessr.service.image import ImageEditService
from nationguessr.settings import FactsGenerationStrategy, Settings

settings = Settings()

logging_level = settings.logging_level.value
logger = logging.getLogger()
logger.setLevel(logging_level)

# Instantiate Bot, Dispatcher, and Router in the global scope, not in the handler function.
# This avoids duplicating the Router instance in the Dispatcher, which prevents a `RuntimeError`.
# See `include_router` method for more details:
#
# https://docs.aiogram.dev/en/latest/_modules/aiogram/dispatcher/router.html#Router.include_router
bot = Bot(
    settings.token,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN, protect_content=True),
)
state_storage = DynamoDBStorage(
    settings.aws_access_key,
    settings.aws_secret_key,
    settings.aws_fsm_table_name,
    settings.aws_region,
)
dp = Dispatcher(storage=state_storage)
dp.include_router(root_router)


async def main(update_event) -> None:
    text_font_path = os.path.join(
        settings.assets_folder, "fonts", "Poppins-ExtraBold.ttf"
    )
    image_edit_service = ImageEditService(text_font_path, settings.default_text_color)

    update_obj = types.Update(**update_event)

    match settings.fact_generation_strategy:
        case FactsGenerationStrategy.LOCAL_ZIPFILE:
            primary_strategy = GenerationFromZipStrategy(settings)
            facts_game_service = GuessingFactsGameService(primary_strategy, settings)
        case FactsGenerationStrategy.GENERATIVE_AI:
            fallback_strategy = GenerationFromZipStrategy(settings)
            primary_strategy = GenerationFromGptStrategy(settings, fallback_strategy)
            facts_game_service = GuessingFactsGameService(primary_strategy, settings)
        case _:
            raise ValueError("Unsupported fact generation strategy")

    await dp.feed_update(
        bot=bot,
        update=update_obj,
        facts_game_service=facts_game_service,
        image_edit_service=image_edit_service,
        app_settings=settings,
    )


def handler(event, _):
    if settings.secret_token is not None:
        update_headers = event.get("headers", {})
        update_secret_token = update_headers.get("x-telegram-bot-api-secret-token")

        if update_secret_token is None or update_secret_token != settings.secret_token:
            origin_address = update_headers.get("x-forwarded-for", "0.0.0.0")
            logger.warning(
                f"Received an unauthorized external request from '{origin_address}' with missing secret token"
            )
            return {"statusCode": 403}

    update_event = json.loads(event.get("body", "{}"))
    loop = asyncio.get_event_loop()

    logger.debug(f"Received an update event: {update_event}")

    if not settings.token:
        logger.error(
            "API Token is empty or invalid. Set it in `VAR_TOKEN` environment variable"
        )
        return {"statusCode": 400}

    try:
        loop.run_until_complete(main(update_event))
    except Exception as ex:
        logger.error(f"Error while executing lambda: '{ex}'")
        return {"statusCode": 500}

    return {"statusCode": 204}
