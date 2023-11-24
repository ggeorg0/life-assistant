import logging
from datetime import datetime, time, timezone, timedelta
import asyncio
from random import shuffle
from typing import Callable, Awaitable, Literal

from telegram import Update
from telegram.ext import (ApplicationBuilder,
                          Application,
                          CommandHandler, 
                          ContextTypes, 
                          MessageHandler,
                          filters,
                          Defaults,
                          CallbackContext,
                          JobQueue)

from notion_client import AsyncClient, APIErrorCode, APIResponseError
from notion_client.helpers import async_iterate_paginated_api, is_full_page

from config import BOT_TOKEN, INTEGRATION_TOKEN
from config import TG_TARGET_ID, INBOX_DATABASE_ID
from config import CALENDAR_DATABASE_ID
from config import CURRENT_TASKS_ID
from config import DEPTH_LIMIT, PAGE_SIZE

from plugins import PluginManager
from notion import Notion
from tools import protect_for_html

logging.basicConfig(
        format='%(asctime)s %(levelname)s %(name)s - %(message)s',
        level=logging.WARN)

TZONE = timezone(timedelta(hours=3))


HELP_MESSAGE = """Бот системы продуктивности.
- /inbox - показать задачи в корзине
- /del n - удалить последние n задач из корзины
- /morning - показать утренее сообщение сейчас
- /rtask - случайная задача из Current Tasks
- /help - показать это сообщение
- /reschedule_notifications - удалить и создать заново отложенные уведомления расширений и плагинов
- /schedule - расписание университета на сегодня 
- /tschedule - расписание университета на завтра
"""

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
            events.append(protect_for_html(line))
    if events:
        lines.append("<b>События календаря:</b>")
        events[-1] = events[-1] + '\n'
        lines += events
    lines.append('<b>5 случайных текущих задач:</b>')
    shuffle(current_tasks)
    for task in current_tasks[:5]:
        lines.append(protect_for_html(' > ' + task))
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
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, protect_for_html(HELP_MESSAGE)) 

async def send_custom_message(context: CallbackContext):
    # TODO: ~Callable[[TYPE], Awaitable[TYPE]] type hint
    """send a message callback. \n
    Use `data` argument to pass another callback that return `str` (text of message), 
    when you passing this function to `Application.job_queue` \n
    Example:
    ```
    def my_text():
        return "text of my scheduled message"

    job_queue.run_daily(send_custom_message,
                        time(hour=17, minute=00),
                        data=my_text)
    ```
    """
    # if not context.job: return
    if isinstance(context.job.data, Callable):
        message = await context.job.data()
    else:
        logging.error("context.job.data is not Callable"
                      f"job.name=({context.job.name})")
        return
    if message:
        await context.bot.send_message(TG_TARGET_ID, message,
                                       parse_mode='HTML')
    else:
        logging.error("Trying to send empty message "
                      f"job.name=({context.job.name})")
        
async def do_custom_action(context: CallbackContext):
    """bot wrapper of callback of plugin action. \n
    Use `data` argument to plugin callback, 
    when you passing this function to `Application.job_queue` \n
    Example:
    ```
    def my_action():
        # whatever is here
        ...

    job_queue.run_daily(do_custom_action,
                        time(hour=17, minute=00),
                        data=my_action)
    ```
    """
    # if not context.job: return
    if isinstance(context.job.data, Callable):
        await context.job.data()
    else:
        logging.error("context.job.data is not Callable"
                      f"job.name=({context.job.name})")
        
def reschedule_plugin_actions(job_queue: JobQueue):
    for plg in plugin_manager.loaded_plugins:
        for plg_job in job_queue.get_jobs_by_name(plg.name):
            plg_job.schedule_removal()
        for dt, m_callback, period in plg.message_callabacks:
            match period:
                case "daily":
                    job_queue.run_daily(send_custom_message, time=dt.time(),
                                        name=plg.name, data=m_callback)
                case "once":
                    job_queue.run_once(send_custom_message, when=dt,
                                       name=plg.name, data=m_callback)
                case "monthly":
                    job_queue.run_monthly(send_custom_message, when=dt.time(),
                                          name=plg.name, day=dt.day,
                                          data=m_callback)
        for dt, act_callback, period in plg.actions_callbacks:
            match period:
                case "daily":
                    job_queue.run_daily(do_custom_action, time=dt.time(),
                                        name=plg.name, data=act_callback)
                case "once":
                    job_queue.run_once(do_custom_action, when=dt,
                                       name=plg.name, data=act_callback)
                case "monthly":
                    job_queue.run_monthly(do_custom_action, when=dt.time(),
                                          day=dt.day, name=plg.name,
                                          data=act_callback)

@validate_user                    
async def reschedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        reschedule_plugin_actions(context.job_queue)
        await context.bot.send_message(chat_id, "Done!")
    except Exception as exc:
        await context.bot.send_message(chat_id, str(exc))

def plg_method_callback_factory(plg_name, plg_method) -> Callable[..., Awaitable]:
    @validate_user
    async def bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        plg = plugin_manager.get_enabled_plugin(plg_name)
        if plg:
            method = getattr(plg, plg_method)
            data = await method(*context.args)
            if type(data) == str:
                await context.bot.send_message(TG_TARGET_ID, text=data,
                                               parse_mode='HTML')
        else:
            logging.warning(f"Plugin {plg_name} is not enabled. "
                            "(unsuccessful try of execution)")
    return bot_callback

def bound_plg_method(app: Application,
                     command: str,
                     method_sorce: str):
    """### Use this method to bound plugin method to the bot command.\n
    For `method_sorce` argument you shoud separate plugin name 
    (not name of plugin class) and method name with colon `:` 
    (see expamle)
    ### Example:
    ```
    app = ApplicationBuilder().token(TOKEN).build()

    bound_plg_method_to_cmd(app, 'weather', 'WeatherPlugin:get_weather')
    """
    plg_name, plg_method = method_sorce.split(':')
    callback = plg_method_callback_factory(plg_name, plg_method)
    app.add_handler(CommandHandler(command, callback))


if __name__ == "__main__":
    nnotion = Notion()

    plugin_manager = PluginManager("tg-bot/plugins").load_plugins()

    defaults = Defaults(tzinfo=TZONE)
    app = ApplicationBuilder().token(BOT_TOKEN).defaults(defaults).build()
    app.add_handler(CommandHandler("inbox", last_tasks))
    app.add_handler(CommandHandler("del", delete_last_n))
    # app.add_handler(CommandHandler("morning", morning_message))
    app.add_handler(CommandHandler('rtask', random_current_task))
    app.add_handler(CommandHandler('help', help))
    app.add_handler(CommandHandler('reschedule_notifications', reschedule))

    bound_plg_method(app, 'morning', "MorningSummary:morning_message")
    bound_plg_method(app, 'schedule', "UniSchedule:today")
    bound_plg_method(app, 'tschedule', "UniSchedule:tomorrow")
    bound_plg_method(app, 'schedule_settime', "UniSchedule:set_sending_time")

    reschedule_plugin_actions(app.job_queue)

    app.add_handler(MessageHandler(filters.TEXT, insert_into_notion))
    app.run_polling()
