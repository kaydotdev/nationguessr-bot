import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from nationguessr.app.handlers import root_router
from nationguessr.service.fsm.storage import DynamoDBStorage
from nationguessr.service.game import (
    GenerationFromZipStrategy,
    GuessingFactsGameService,
)
from nationguessr.settings import Settings

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
    facts_generation_strategy = GenerationFromZipStrategy(settings)
    facts_game_service = GuessingFactsGameService(facts_generation_strategy, settings)

    bot = Bot(settings.token, parse_mode=ParseMode.MARKDOWN)
    dp = Dispatcher(storage=state_storage)
    dp.include_router(root_router)

    await dp.start_polling(
        bot,
        skip_updates=True,
        facts_game_service=facts_game_service,
        app_settings=settings,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging_level, stream=sys.stdout)
    asyncio.run(main())
