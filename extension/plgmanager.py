from typing import TYPE_CHECKING
from itertools import count
import logging
if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from datetime import datetime

from extension.abstractplugin import AbstractPlugin


class PluginManager:
    # Singletone class
    _ids = count(0)
    _loaded_plugins: dict[str, AbstractPlugin]

    def __init__(self, plugins: Iterable[AbstractPlugin] = []):
        self.id = next(self._ids)
        if self.id > 1:
            raise RuntimeError("There are additional PluginManager instance")
        self.set_plugins(plugins)

    def user_commands(self) -> Iterable[tuple[str, str, Callable]]:
        logging.info("Plugin Manager: loading user commands")
        for plg_name, p in self._loaded_plugins.items():
            if p.isenabled:
                for command, action in p.user_commands():
                    yield (plg_name, command, action)
            else:
                logging.info(f"Plugin Manager: skipping [{plg_name}]"
                             " (not enabled)")

    def daily_events(self) -> Iterable[tuple[str, datetime, Callable]]:
        logging.info("Plugin Manager: loading daily events")
        for plg_name, p in self._loaded_plugins.items():
            if p.isenabled:
                for dt, action in p.daily_events():
                    yield (plg_name, dt, action)
            else:
                logging.info(f"Plugin Manager: skipping [{plg_name}]"
                             " (not enabled)")

    def monthly_events(self) -> Iterable[tuple[str, datetime, Callable]]:
        logging.info("Plugin Manager: loading monthly events")
        for plg_name, p in self._loaded_plugins.items():
            if p.isenabled:
                for dt, action in p.monthly_events():
                    yield (plg_name, dt, action)
            else:
                logging.info(f"Plugin Manager: skipping [{plg_name}]"
                             " (not enabled)")


    def disorder_events(self) -> Iterable[tuple[str, datetime, Callable]]:
        logging.info("Plugin Manager: loading disordered events")
        for plg_name, p in self._loaded_plugins.items():
            if p.isenabled:
                for dt, action in p.disordered_events():
                    yield (plg_name, dt, action)
            else:
                logging.info(f"Plugin Manager: skipping [{plg_name}]"
                             " (not enabled)")


    def set_plugins(self, plugins: Iterable[AbstractPlugin]):
        self._loaded_plugins = {p.name: p for p in plugins}

    def _get_plugin(self, name):
        return self._loaded_plugins[name]

    def enable_plugin(self, name):
        self._get_plugin(name).enable()

    def diable_plugin(self, name):
        self._get_plugin(name).disable()

