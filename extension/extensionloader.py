from datetime import datetime
import logging
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any

from telegram import Update
from telegram.ext import (Application,
                          CommandHandler,
                          ContextTypes,
                          MessageHandler,
                          filters,
                          CallbackContext,
                          JobQueue)

from extension import PluginManager
from extension.plugins import (
    # UniSchedule,
    # MorningSummary,
    RandomCurrentTask,
    )
from tools import validate_user, protect_for_html
from config import TG_CHAT_ID
from extension.plgtyples import ActionT

# TODO: automatic help command by all plugins
# TODO: rename callbackreturn
# TODO: reorder imports


# command --> str , str | event, event
#       where `event` --> (datetime and plugin.action)


class ExtensionLoader:
    __slots__ = (
        "_plugins_dir",
        "_plg_manager"
    )
    _plugins_dir: str
    _plg_manager: PluginManager

    def __init__(self, plugins_dir: str) -> None:
        self._plugins_dir = plugins_dir
        self._plg_manager = PluginManager()

    def load_plugins(self):
        # TODO: add dynamic loading from `self._plugins_dir`
        # plugins = (UniSchedule(), MorningSummary(), RandomCurrentTask())
        plugins = (RandomCurrentTask(), )
        self._plg_manager.set_plugins(plugins)

    def load_commands(self, app: Application):
        for plg_name, cmd, action in self._plg_manager.user_commands():
            callback = self.make_command_callback(action, plg_name)
            app.add_handler(CommandHandler(cmd, callback))
            logging.info(f"[{plg_name}]: adding command /{cmd}")

    def make_command_callback(self, action: ActionT, plg_name: str) \
            -> Callable[..., Coroutine[Any, Any, None]]:
        @validate_user
        async def callback(update: Update,
                           context: ContextTypes.DEFAULT_TYPE):
            command_args = context.args or ()
            try:
                act_result = await action(*command_args)
            except Exception as e:
                logging.error(f"[{plg_name}] user triggered action "
                              f"'{action.__name__}' FAILED \n{e}")
                return None
            if act_result.message:
                await context.bot.send_message(
                    update.effective_chat.id,
                    protect_for_html(act_result.message)
                )
            elif not (act_result.next_action is None
                      or act_result.next_datetime is None):
                cb = self.create_event_callback(
                    act_result.next_action,
                    plg_name
                )
                context.job_queue.run_once(
                    callback=cb,
                    when=act_result.next_datetime,
                    name=plg_name,
                    chat_id=update.effective_chat.id
                )
            else:
                logging.info(f"[{plg_name}] executed from user "
                             "command: {action.__name__}")
        return callback

    def load_daily_events(self, app: Application):
        for plg_name, dt, action in self._plg_manager.daily_events():
            callback = self.create_event_callback(action, plg_name)
            app.job_queue.run_daily(
                callback,
                time=dt.time(),
                name=plg_name,
                chat_id=TG_CHAT_ID
            )

    def load_disordered_events(self, app: Application):
        for plg_name, dt, action in self._plg_manager.disorder_events():
            callback = self.create_event_callback(action, plg_name)
            app.job_queue.run_once(
                callback,
                when=dt,
                name=plg_name,
                chat_id=TG_CHAT_ID)

    def load_monthly_events(self, app: Application):
        for plg_name, dt, action in self._plg_manager.monthly_events():
            callback = self.create_event_callback(action, plg_name)
            app.job_queue.run_monthly(
                callback,
                when=dt.time(),
                day=dt.day,
                name=plg_name,
                chat_id=TG_CHAT_ID)

    def create_event_callback(self, action: ActionT, plg_name: str):
        async def callback(context: CallbackContext):
            try:
                act_result = await action()
            except Exception as e:
                logging.error(f"[{plg_name}] user triggered action "
                              f"'{action.__name__}' FAILED \n{e}")
                return None
            if act_result.message:
                context.bot.send_message(
                    context.job.chat_id,
                    protect_for_html(act_result.message)
                )
            elif not (act_result.next_action is None
                      or act_result.next_datetime is None):
                cb = self.create_event_callback(
                    act_result.next_action,
                    plg_name
                )
                context.job_queue.run_once(
                    callback=cb,
                    when=act_result.next_datetime,
                    name=plg_name,
                    chat_id=context.job.chat_id
                )
            else:
                logging.info(f"[{plg_name}] executed event "
                             "action: {action.__name__}")
        return callback

