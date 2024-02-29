#!/usr/bin/env python

import logging
from typing import Callable

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    Defaults,
)

from notion_client import APIErrorCode, APIResponseError

from config import (
    BOT_TOKEN,
    DEPTH_LIMIT,
    TIMEZONE
)

from extension import ExtensionLoader
from notion import Notion
from tools import protect_for_html, validate_user

logging.basicConfig(
        format='%(asctime)s %(levelname)s %(name)s - %(message)s',
        level=logging.INFO,
        datefmt='%y-%m-%d %H:%M:%S',
)


HELP_MESSAGE = """Бот системы продуктивности.
- /inbox - показать задачи в корзине
- /del n - удалить последние n задач из корзины
- /morning - показать утреннее сообщение сейчас
- /rtask /task - случайная задача из Current Tasks
- /done - отметить последнюю выбранную случайную задачу выполненой
- /undone - отметить последнюю задачу как невыполненную (см. /done )
- /help - показать это сообщение
- /reschedule_notifications - удалить и создать заново отложенные уведомления расширений и плагинов
- /schedule - расписание университета на сегодня
- /tschedule - расписание университета на завтра
- /schedule_settime HH MM SS - установить время отправки расписания университета

"""

nnotion: Notion

async def _call_api_when_available(notion_api_action: Callable,
                                   context: ContextTypes.DEFAULT_TYPE,
                                   depth=0):
    if depth > DEPTH_LIMIT:
        logging.error("The number of attempts to send the task to Notion exceeded {DEPTH_LIMIT}")
        return
    try:
        await notion_api_action()
    except APIResponseError as error:
        if error.code == APIErrorCode.ServiceUnavailable:
            timing = 60 * depth * 2
        if error.code == APIErrorCode.RateLimited:
            timing = 3 * depth * 2
        else:
            raise error
        context.job_queue.run_once(_call_api_when_available,
                                   timing,
                                   name='pending_notion_api',
                                   job_kwargs={"notion_api_action": notion_api_action,
                                               "context": context,
                                               "depth": depth + 1})

@validate_user
async def add_to_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    create_notion_page = lambda: nnotion.create_page_in_inbox(update.effective_message.text)
    try:
        await create_notion_page()
        await update.effective_message.reply_text("added to Notion")
    except APIResponseError as error:
        if error.code == APIErrorCode.ServiceUnavailable:
            timing = 60
            await context.bot.send_message(chat_id, "Service Unavailable Err, "
                                     "Request will be sended again later")
        if error.code == APIErrorCode.RateLimited:
            timing = 3
            await context.bot.send_message(chat_id, "Rate Limited Err, "
                                     "Request will be sended again later")
        else:
            raise APIResponseError
        context.job_queue.run_once(_call_api_when_available,
                                   timing,
                                   name='pending_notion_api',
                                   job_kwargs={"notion_api_action": create_notion_page,
                                               "context": context,
                                               "depth": 1})

@validate_user
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, protect_for_html(HELP_MESSAGE))

if __name__ == "__main__":
    nnotion = Notion()

    defaults = Defaults(tzinfo=TIMEZONE, parse_mode='HTML')
    app = ApplicationBuilder().token(BOT_TOKEN).defaults(defaults).build()

    extensions = ExtensionLoader()
    # TODO: hide this method (`load_plugins`) from public
    #       cause it is really easy to foget it.
    extensions.load_plugins()
    extensions.load_commands(app)
    extensions.load_daily_events(app)
    extensions.load_monthly_events(app)
    extensions.load_disordered_events(app)

    app.add_handler(CommandHandler('help', help))

    app.add_handler(MessageHandler(filters.TEXT, add_to_inbox))


    app.run_polling()
