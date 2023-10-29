import logging

from telegram import Update
from telegram.ext import (ApplicationBuilder, 
                          CommandHandler, 
                          ContextTypes, 
                          MessageHandler,
                          filters)

from notion_client import AsyncClient, APIErrorCode, APIResponseError

from config import BOT_TOKEN, INTEGRATION_TOKEN
from config import TARGET_ID, INBOX_DATABASE_ID
from config import DEPTH_LIMIT

notion: AsyncClient


def validate_user(func):
    async def wrapper(update: Update, *args, **kwargs):
        if update.effective_chat.id == TARGET_ID:
            return await func(update, *args, **kwargs)
        
    return wrapper
        

@validate_user
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

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
        if error.code == APIErrorCode.RateLimited:
            timing = 3
        else:
            raise APIResponseError
        context.job_queue.run_once(_call_api_when_available,
                                   timing,
                                   job_kwargs={"notion_api_action": create_notion_page,
                                               "context": context,
                                               "depth": 1})
            

    
# смотреть последние отправленные задания



if __name__ == "__main__":
    notion = AsyncClient(auth=INTEGRATION_TOKEN)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("hello", hello))

    app.add_handler(MessageHandler(filters.TEXT, insert_into_notion))
    app.run_polling()

