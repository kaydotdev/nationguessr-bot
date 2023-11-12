import asyncio
import logging
import os
import json

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types.bot_command import BotCommand


START_MESSAGE = """🌎 Hi there, I'm Nationguessr! With me, you get to test your knowledge about countries from all over the world by trying to guess them based on random facts about their history, culture, geography, and much more!

🔁 To play a quiz from the beginning use /restart command.
🔝 To see your highest score in quiz use /score command.
🆑 To clear all your high score history use /clear command.

Here is your first question:"""


logger = logging.getLogger()
logger.setLevel(logging.INFO)


TOKEN = os.getenv("BOT_TOKEN") or ""

dp = Dispatcher()
bot = Bot(TOKEN, parse_mode=ParseMode.MARKDOWN)


@dp.message(CommandStart())
async def start_handler(message: types.Message) -> None:
    await message.answer(START_MESSAGE)


@dp.message(Command(BotCommand(command="restart", description="Start your quiz from the very beginning")))
async def restart_handler(message: types.Message) -> None:
    await message.answer("TODO: implement restart command.")


@dp.message(Command(BotCommand(command="score", description="View your top score in quiz")))
async def score_handler(message: types.Message) -> None:
    await message.answer("TODO: implement score command.")


@dp.message(Command(BotCommand(command="clear", description="Clear your score table")))
async def clear_handler(message: types.Message) -> None:
    await message.answer(
        "Now your high score board is empty. Use /start command to play a new game!"
    )


async def main(update_event) -> None:
    update_obj = types.Update(**update_event)
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
