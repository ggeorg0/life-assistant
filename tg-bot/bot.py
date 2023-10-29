import logging

from telegram import Update
from telegram.ext import (ApplicationBuilder, 
                          CommandHandler, 
                          ContextTypes, 
                          MessageHandler,
                          filters)

from notion_client import AsyncClient, APIErrorCode, APIResponseError
from notion_client.helpers import iterate_paginated_api, is_full_page

from config import BOT_TOKEN, INTEGRATION_TOKEN
from config import TARGET_ID, INBOX_DATABASE_ID
from config import DEPTH_LIMIT, PAGE_SIZE


notion: AsyncClient


def validate_user(func):
    async def wrapper(update: Update, *args, **kwargs):
        if update.effective_chat.id == TARGET_ID:
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
                                   job_kwargs={"notion_api_action": notion_api_action,
                                               "context": context,
                                               "depth": depth + 1})

async def _create_page(title: str):
    return await notion.pages.create(
        parent={'database_id': INBOX_DATABASE_ID},
        properties={
            'Name': {
            'title': [{'text': {'content': title}}]
        }, 
    })

@validate_user
async def insert_into_notion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    create_notion_page = lambda: _create_page(update.effective_message.text)
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
                                   job_kwargs={"notion_api_action": create_notion_page,
                                               "context": context,
                                               "depth": 1})
        
def _protect_for_html(text_data):
    return text_data.replace('&', '&amp;')\
                    .replace('<', '&lt;')\
                    .replace('>', '&gt;')

async def last_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        results = await notion.databases.query(database_id=INBOX_DATABASE_ID, 
                                               sorts=[{"property": "Created",
                                                       "direction": "descending"}],
                                               page_size=PAGE_SIZE)
        titles = ["<b>List of tasks</b>"]
        for i, task in enumerate(results["results"]):
            if is_full_page(task):
                task_title = task["properties"]["Name"]["title"]
                if task_title:
                    line = f"{i + 1}. {task_title[0]['plain_text']}"
                    titles.append(_protect_for_html(line))
        if results["next_cursor"] != None:
            titles.append("<b>Visit Notion to see full list...</b>")
        titles = "\n".join(titles)
        await context.bot.send_message(chat_id=update.effective_chat.id, 
                                       text=titles, 
                                       parse_mode='HTML')
    except APIResponseError as error:
        context.bot.send_message(f"Error (code={error.code}). Try again later.")

async def archive_n_pages(count=1):
    results = await notion.databases.query(database_id=INBOX_DATABASE_ID, 
                                           sorts=[{"property": "Created",
                                                   "direction": "descending"}],
                                           page_size=count)
    for p in results["results"]:
        await notion.pages.update(page_id=p['id'], archived=True)

async def delete_last_n(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        num_of_pages = int(context.args[0])
        if num_of_pages > 10:
            raise ValueError
        await archive_n_pages(num_of_pages)
        await context.bot.send_message(chat_id, f"{num_of_pages} pages have been deleted")
    except APIResponseError:
        await context.bot.send_message(chat_id, "Some pages could not be deleted. "
                                                "(code={error.code}). Try again later.")
    except ValueError:
        await context.bot.send_message(chat_id, "Invalid number of pages"
                                                "(Should be > 1 and <= 10)")

if __name__ == "__main__":
    notion = AsyncClient(auth=INTEGRATION_TOKEN)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("inbox", last_tasks))
    app.add_handler(CommandHandler("del", delete_last_n))

    app.add_handler(MessageHandler(filters.TEXT, insert_into_notion))
    app.run_polling()

