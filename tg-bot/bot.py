import logging
from datetime import datetime, time, timezone, timedelta
import asyncio
from random import shuffle

from telegram import Update
from telegram.ext import (ApplicationBuilder, 
                          CommandHandler, 
                          ContextTypes, 
                          MessageHandler,
                          filters,
                          Defaults)

from notion_client import AsyncClient, APIErrorCode, APIResponseError
from notion_client.helpers import async_iterate_paginated_api, is_full_page

from config import BOT_TOKEN, INTEGRATION_TOKEN
from config import TG_TARGET_ID, INBOX_DATABASE_ID
from config import CALENDAR_DATABASE_ID
from config import CURRENT_TASKS_ID
from config import DEPTH_LIMIT, PAGE_SIZE

from plugins import PluginManager
from notion import Notion
from tools import _protect_for_html

logging.basicConfig(
        format='%(asctime)s %(levelname)s %(name)s - %(message)s',
        level=logging.WARN)

TZONE = timezone(timedelta(hours=3))


# notion: AsyncClient
nnotion: Notion
plugin_manager: PluginManager


def validate_user(func):
    async def wrapper(update: Update, *args, **kwargs):
        if update.effective_chat.id == TG_TARGET_ID:
            return await func(update, *args, **kwargs)
        
    return wrapper
        

async def _call_api_when_available(notion_api_action: callable,
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
            raise APIResponseError
        context.job_queue.run_once(_call_api_when_available, 
                                   timing,
                                   name='pending_notion_api',
                                   job_kwargs={"notion_api_action": notion_api_action,
                                               "context": context,
                                               "depth": depth + 1})

# async def _create_page(title: str):
#     return await notion.pages.create(
#         parent={'database_id': INBOX_DATABASE_ID},
#         properties={
#             'Name': {
#             'title': [{'text': {'content': title}}]
#         }, 
#     })

@validate_user
async def insert_into_notion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    create_notion_page = lambda: nnotion.create_page_in_inbox(update.effective_message.text)
    try:
        await create_notion_page()
        await update.effective_message.reply_text("added to Notion")
    except APIResponseError as error:
        if error.code == APIErrorCode.ServiceUnavailable:
            timing = 60
            context.bot.send_message(chat_id, "Service Unavailable Err, "
                                     "Request will be sended again later")
        if error.code == APIErrorCode.RateLimited:
            timing = 3
            context.bot.send_message(chat_id, "Rate Limited Err, "
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
async def last_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        titles = await nnotion.last_inbox_pages()
        await context.bot.send_message(chat_id=update.effective_chat.id, 
                                       text="\n".join(titles), 
                                       parse_mode='HTML')
    except APIResponseError as error:
        context.bot.send_message(f"Error (code={error.code}). Try again later.")

@validate_user
async def delete_last_n(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        num_of_pages = int(context.args[0])
        if num_of_pages > 10:
            raise ValueError
        await nnotion.archive_n_pages(num_of_pages)
        await context.bot.send_message(chat_id, f"{num_of_pages} pages have been deleted")
    except APIResponseError:
        await context.bot.send_message(chat_id, "Some pages could not be deleted. "
                                                "(code={error.code}). Try again later.")
    except ValueError:
        await context.bot.send_message(chat_id, "Invalid number of pages"
                                                "(Should be > 1 and <= 10)")
        
def _fmt_event_time(event):
    result = ''
    if event['end']:
        result = event['start'].strftime(" %d/%m")
    if event['start'].hour or event['start'].minute:
        result = result + event['start'].strftime(" %H:%M")
    if event['end']:
        result = result + event['end'].strftime(" — %d/%m")
        if event['end'].hour or event['end'].minute:
            result = result + event['end'].strftime(" %H:%M")
    return result

def gather_base_summary(calendar, current_tasks):
    lines = []
    events = [] 
    now = datetime.now()
    for event in calendar:
        if now.date() == event['start'].date() or (now.date() >= event['start'].date()
                                                   and event['end']
                                                   and event['end'].date() >= now.date()):
            line = ' > ' + event['title'] + _fmt_event_time(event)
            events.append(_protect_for_html(line))
    if events:
        lines.append("<b>События календаря:</b>")
        events[-1] = events[-1] + '\n'
        lines += events
    lines.append('<b>5 случайных текущих задач:</b>')
    shuffle(current_tasks)
    for task in current_tasks[:5]:
        lines.append(_protect_for_html(' > ' + task))
    lines[-1] = lines[-1] + '\n'
    return lines

async def gather_morning_message():
    calendar = await nnotion.today_calendar_events()
    tasks = await nnotion.current_tasks()
    message_data = gather_base_summary(calendar, tasks)
    plugin_manager.plugins_apply(message_data)
    return "\n".join(message_data)

async def send_morning_message(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(TG_TARGET_ID, 
                                   await gather_morning_message(),
                                   parse_mode='HTML')

@validate_user
async def morning_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(update.effective_chat.id,
                                   await gather_morning_message(),
                                   parse_mode='HTML')

@validate_user
async def random_current_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tasks = await nnotion.current_tasks()
    shuffle(tasks)
    await context.bot.send_message(chat_id, tasks[0])

@validate_user
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.bot.send_message
    raise NotImplementedError
    # TODO

if __name__ == "__main__":
    nnotion = Notion(token=INTEGRATION_TOKEN)

    plugin_manager = PluginManager("tg-bot/plugins").load_plugins()

    defaults = Defaults(tzinfo=TZONE)
    app = ApplicationBuilder().token(BOT_TOKEN).defaults(defaults).build()
    app.add_handler(CommandHandler("inbox", last_tasks))
    app.add_handler(CommandHandler("del", delete_last_n))
    app.add_handler(CommandHandler("morning", morning_message))
    app.add_handler(CommandHandler('rtask', random_current_task))
    app.add_handler(CommandHandler('help', help))
    app.job_queue.run_daily(send_morning_message, 
                            time(hour=8, minute=30),
                            name='morning_message')
    app.add_handler(MessageHandler(filters.TEXT, insert_into_notion))
    app.run_polling()
