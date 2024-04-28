import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
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


async def main():
    if not settings.token:
        logger.error(
            "API Token is empty or invalid. Set it in `VAR_TOKEN` environment variable"
        )
        sys.exit(1)

    state_storage = DynamoDBStorage(
        settings.aws_access_key,
        settings.aws_secret_key,
        settings.aws_fsm_table_name,
        settings.aws_region,
    )

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

    text_font_path = os.path.join(
        settings.assets_folder, "fonts", "Poppins-ExtraBold.ttf"
    )
    image_edit_service = ImageEditService(text_font_path, settings.default_text_color)

    bot = Bot(
        settings.token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.MARKDOWN, protect_content=True
        ),
    )
    dp = Dispatcher(storage=state_storage)
    dp.include_router(root_router)

    await dp.start_polling(
        bot,
        skip_updates=True,
        facts_game_service=facts_game_service,
        image_edit_service=image_edit_service,
        app_settings=settings,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging_level, stream=sys.stdout)
    asyncio.run(main())
