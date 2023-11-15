import asyncio
import logging
import json

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode

from handlers import root_router
from fsm import state_storage
from vars import TOKEN


logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def main(update_event) -> None:
    update_obj = types.Update(**update_event)

    bot = Bot(TOKEN, parse_mode=ParseMode.MARKDOWN)
    dp = Dispatcher(storage=state_storage)
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
