from __future__ import annotations
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackContext
)

from extension import PluginManager, PluginLoader
from extension.plgtyples import ActionT
from config import TG_CHAT_ID, PLUGINS_DIR
from tools import validate_user

# TODO: automatic help command by all plugins


class ExtensionLoader:
    __slots__ = (
        "_plg_manager",
        "_plg_loader"
    )
    _plg_manager: PluginManager
    _plg_loader: PluginLoader

    def __init__(self, plugins_dir: str) -> None:
        self._plg_manager = PluginManager()
        self._plg_loader = PluginLoader(PLUGINS_DIR)

    def load_plugins(self):
        plugins = self._plg_loader.load()
        self._plg_manager.set_plugins(plugins)

    def load_commands(self, app: Application):
        for plg_name, cmd, action in self._plg_manager.user_commands():
            callback = self.make_command_callback(action, plg_name)
            app.add_handler(CommandHandler(cmd, callback))
            logging.info(f"[{plg_name}]: adding command /{cmd}")

    def make_command_callback(self, action: ActionT, plg_name: str):
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
                    act_result.message
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
                logging.error(f"[{plg_name}] triggered action "
                              f"'{action.__name__}' FAILED \n{e}")
                return None
            if act_result.message:
                context.bot.send_message(
                    context.job.chat_id,
                    act_result.message
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

