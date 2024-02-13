import logging
import importlib.util
from inspect import isclass
import traceback
import os
from collections.abc import Callable, Coroutine
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackContext
)
from extension import PluginManager, AbstractPlugin
from tools import validate_user
from config import TG_CHAT_ID, PLUGINS_DIR
from extension.plgtyples import ActionT
from pathlib import Path

# TODO: automatic help command by all plugins


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
        plugin_files = [file for file in os.listdir(PLUGINS_DIR)
                        if file.endswith('plugin.py')]
        plugins = []
        for pf in plugin_files:
            try:
                plugins += self._load_plugin_file(pf)
            except Exception as e:
                logging.error(f"cannot load file `{pf}`, reason:\n"
                              f"{''.join(traceback.format_exception(e))}")
        self._plg_manager.set_plugins(plugins)

    def _load_plugin_file(self, filename) -> list[AbstractPlugin]:
            path, name = self._module_path_name(PLUGINS_DIR, filename)
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return self._fetch_plugins_from_module(module)

    def _module_path_name(self, path: str, filename: str) -> tuple[Path, str]:
        filepath = Path(path, filename)
        module_name = filename[:-3] # remove '.py'
        return filepath, module_name

    def _fetch_plugins_from_module(self, module):
        module_dir = [v for v in dir(module) if not v.startswith('__')]
        instances = []
        for obj in module_dir:
            module_attr = getattr(module, obj)
            if (isclass(module_attr)
                    and issubclass(module_attr, AbstractPlugin)
                    and module_attr is not AbstractPlugin):
                instances.append(module_attr())
        return instances

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

