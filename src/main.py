import asyncio
import logging
import sqlite3
import sys

import nationguessr.app.settings as settings
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from nationguessr.app.handlers import root_router
from nationguessr.service.fsm.storage import DynamoDBStorage

logger = logging.getLogger()
logger.setLevel(settings.LOGGING_LEVEL)


async def main():
    if not settings.TOKEN:
        logger.error(
            "API Token is empty or invalid. Set it in `BOT_TOKEN` environment variable"
        )
        sys.exit(1)

    with sqlite3.connect(settings.SQLITE_DB_PATH) as conn:
        logger.debug(
            "Successfully created DB connection instance from file:"
            f" '{settings.SQLITE_DB_PATH}'"
        )

        state_storage = DynamoDBStorage(
            settings.AWS_ACCESS_KEY,
            settings.AWS_SECRET_KEY,
            settings.AWS_FSM_TABLE_NAME,
            settings.AWS_REGION,
        )
        bot = Bot(settings.TOKEN, parse_mode=ParseMode.MARKDOWN)
        dp = Dispatcher(storage=state_storage)
        dp.include_router(root_router)

        await dp.start_polling(bot, skip_updates=True, db_connection=conn)

        logger.debug("Closing DB connection instance")


if __name__ == "__main__":
    logging.basicConfig(level=settings.LOGGING_LEVEL, stream=sys.stdout)
    asyncio.run(main())
