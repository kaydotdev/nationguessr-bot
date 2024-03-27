import asyncio
import json
import logging
import sqlite3

import nationguessr.app.settings as settings
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from nationguessr.app.handlers import root_router
from nationguessr.service.fsm.storage import DynamoDBStorage

logger = logging.getLogger()
logger.setLevel(settings.LOGGING_LEVEL)

# Instantiate Bot, Dispatcher, and Router in the global scope, not in the handler function.
# This avoids duplicating the Router instance in the Dispatcher, which prevents a `RuntimeError`.
# See `include_router` method for more details:
#
# https://docs.aiogram.dev/en/latest/_modules/aiogram/dispatcher/router.html#Router.include_router
bot = Bot(settings.TOKEN, parse_mode=ParseMode.MARKDOWN)
state_storage = DynamoDBStorage(
    settings.AWS_ACCESS_KEY,
    settings.AWS_SECRET_KEY,
    settings.AWS_FSM_TABLE_NAME,
    settings.AWS_REGION,
)
dp = Dispatcher(storage=state_storage)
dp.include_router(root_router)


async def main(update_event) -> None:
    with sqlite3.connect(settings.SQLITE_DB_PATH) as conn:
        logger.debug(
            "Successfully created DB connection instance from file:"
            f" '{settings.SQLITE_DB_PATH}'"
        )

        update_obj = types.Update(**update_event)
        await dp.feed_update(bot=bot, update=update_obj, db_connection=conn)

        logger.debug("Closing DB connection instance")


def handler(event, _):
    update_event = json.loads(event.get("body", "{}"))
    loop = asyncio.get_event_loop()

    logger.debug(f"Received an update event: {update_event}")

    if not settings.TOKEN:
        logger.error(
            "API Token is empty or invalid. Set it in `BOT_TOKEN` environment variable"
        )
        return {"statusCode": 400}

    try:
        loop.run_until_complete(main(update_event))
    except Exception as ex:
        logger.error(f"Error while executing lambda: '{ex}'")
        return {"statusCode": 500}

    return {"statusCode": 204}
