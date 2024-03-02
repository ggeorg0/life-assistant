from __future__ import annotations
import logging
from traceback import print_exception

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackContext
)

from extension import PluginManager, PluginLoader, AbstractPlugin
from extension.exttypes import ActionT
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

    def __init__(self) -> None:
        self._plg_manager = PluginManager()
        self._plg_loader = PluginLoader(PLUGINS_DIR)

    def load(self, app: Application):
        self.load_plugins()
        self.load_commands(app)
        self.load_daily_events(app)
        self.load_monthly_events(app)
        self.load_disordered_events(app)

    def load_plugins(self):
        plugins = self._plg_loader.load()
        self._plg_manager.set_plugins(plugins)

    def load_commands(self, app: Application):
        for plg, cmd, action in self._plg_manager.user_commands():
            callback = self.make_command_callback(action, plg)
            app.add_handler(CommandHandler(cmd, callback))
            logging.info(f"[{plg.name}]: adding command /{cmd}")

    def make_command_callback(self, action: ActionT, plg: AbstractPlugin):
        @validate_user
        async def callback(update: Update,
                           context: ContextTypes.DEFAULT_TYPE):
            if not plg.isenabled:
                return
            command_args = context.args or ()
            try:
                act_result = await action(*command_args)
            except Exception as e:
                logging.error(f"[{plg.name}] user triggered action "
                              f"'{action.__name__}' FAILED")
                print_exception(e)
                return None
            if act_result.message:
                await context.bot.send_message(
                    update.effective_chat.id,
                    act_result.message
                )
            else:
                logging.info(f"[{plg.name}] executed from user "
                             "command: {action.__name__}")
            if not (act_result.next_action is None
                      or act_result.next_datetime is None):
                cb = self.create_event_callback(
                    act_result.next_action,
                    plg
                )
                context.job_queue.run_once(
                    callback=cb,
                    when=act_result.next_datetime,
                    name=plg.name,
                    chat_id=update.effective_chat.id
                )
        return callback

    def load_daily_events(self, app: Application):
        for plg, dt, action in self._plg_manager.daily_events():
            callback = self.create_event_callback(action, plg)
            app.job_queue.run_daily(
                callback,
                time=dt.time(),
                name=plg.name,
                chat_id=TG_CHAT_ID
            )

    def load_disordered_events(self, app: Application):
        for plg, dt, action in self._plg_manager.disordered_events():
            callback = self.create_event_callback(action, plg)
            app.job_queue.run_once(
                callback,
                when=dt,
                name=plg.name,
                chat_id=TG_CHAT_ID)

    def load_monthly_events(self, app: Application):
        for plg, dt, action in self._plg_manager.monthly_events():
            callback = self.create_event_callback(action, plg)
            app.job_queue.run_monthly(
                callback,
                when=dt.time(),
                day=dt.day,
                name=plg.name,
                chat_id=TG_CHAT_ID)

    def create_event_callback(self, action: ActionT, plg: AbstractPlugin):
        async def callback(context: CallbackContext):
            if not plg.isenabled:
                return
            try:
                act_result = await action()
            except Exception as e:
                logging.error(f"[{plg.name}] triggered action "
                              f"'{action.__name__}' FAILED")
                print_exception(e)
                return None
            if act_result.message:
                await context.bot.send_message(
                    context.job.chat_id,
                    act_result.message
                )
            else:
                logging.info(f"[{plg.name}] executed event "
                             "action: {action.__name__}")
            if not (act_result.next_action is None
                      or act_result.next_datetime is None):
                cb = self.create_event_callback(
                    act_result.next_action,
                    plg
                )
                context.job_queue.run_once(
                    callback=cb,
                    when=act_result.next_datetime,
                    name=plg.name,
                    chat_id=context.job.chat_id
                )
        return callback

