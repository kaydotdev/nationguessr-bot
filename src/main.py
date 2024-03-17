import asyncio
import logging
import sqlite3
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from fsm import state_storage
from handlers import root_router
from vars import LOGGING_LEVEL, SQLITE_DB_PATH, TOKEN

logger = logging.getLogger()
logger.setLevel(LOGGING_LEVEL)


async def main():
    if not TOKEN:
        logger.error(
            "API Token is empty or invalid. Set it in `BOT_TOKEN` environment variable"
        )
        sys.exit(1)

    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        logger.debug(
            f"Successfully created DB connection instance from file: '{SQLITE_DB_PATH}'"
        )

        bot = Bot(TOKEN, parse_mode=ParseMode.MARKDOWN)
        dp = Dispatcher(storage=state_storage)
        dp.include_router(root_router)

        await dp.start_polling(bot, skip_updates=True, db_connection=conn)

        logger.debug("Closing DB connection instance")


if __name__ == "__main__":
    logging.basicConfig(level=LOGGING_LEVEL, stream=sys.stdout)
    asyncio.run(main())
