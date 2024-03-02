#!/usr/bin/env python
import logging
from asyncio import sleep

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
    Defaults,
)

from notion_client import APIErrorCode, APIResponseError

from extension import ExtensionLoader
from mynotion import Notion
from tools import protect_for_html, validate_user
from config import (
    BOT_TOKEN,
    TRY_SEND_LIMIT,
    INITIAL_SEND_TIMING,
    TIMEZONE
)

UNAVAILABLE_ERR = "Service Unavailable Err, request will be send again later"
RATE_ERR = "Rate Limited Err, request will be send again later"
CANNOTSEND_MSG = "Cannot send a message"


logging.basicConfig(
        format='%(asctime)s %(levelname)s %(name)s - %(message)s',
        level=logging.INFO,
        datefmt='%y/%m/%d %H:%M:%S',
)

nnotion: Notion

@validate_user
async def add_to_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    timing = INITIAL_SEND_TIMING
    for _ in range(TRY_SEND_LIMIT):
        try:
            task_text = update.effective_message.text
            safe_text = protect_for_html(task_text)
            await nnotion.create_page_in_inbox(task_text)
            await update.effective_message.reply_text("added to Notion")
            break
        except APIResponseError as notion_err:
            if notion_err.code == APIErrorCode.ServiceUnavailable:
                await context.bot.send_message(chat_id,
                                               f"{UNAVAILABLE_ERR}: {safe_text}")
            elif notion_err.code == APIErrorCode.RateLimited:
                await context.bot.send_message(chat_id,
                                               f"{RATE_ERR}: {safe_text}")
            else:
                raise notion_err
            timing *= 2
            await sleep(timing)
    else:
        logging.error(f'{CANNOTSEND_MSG}: {safe_text}')
        await context.bot.send_message(chat_id,
                                       f'{CANNOTSEND_MSG}: {safe_text}')

if __name__ == "__main__":
    logging.getLogger('httpx').setLevel(logging.WARNING)

    nnotion = Notion()

    defaults = Defaults(tzinfo=TIMEZONE, parse_mode='HTML')
    app = ApplicationBuilder().token(BOT_TOKEN) \
                              .defaults(defaults) \
                              .build()

    extensions = ExtensionLoader()
    extensions.load(app)

    app.add_handler(MessageHandler(filters.TEXT, add_to_inbox, block=False))

    app.run_polling()
