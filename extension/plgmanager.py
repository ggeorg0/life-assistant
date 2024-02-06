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
        # return ("plg_name", "commandname", action), ...
        # TODO join subtuples into one tuple
        ...

    def daily_events(self) -> Iterable[tuple[str, datetime, Callable]]:
        # return ("plg_name", datetime, action), ...
        # TODO
        ...

    def monthly_events(self) -> Iterable[tuple[str, datetime, Callable]]:
        ...

    def disorder_events(self) -> Iterable[tuple[str, datetime, Callable]]:
        ...

    def set_plugins(self, plugins: Iterable[AbstractPlugin]):
        self._loaded_plugins = {p.name: p for p in plugins}

    def _get_plugin(self, name):
        return self._loaded_plugins[name]

    def enable_plugin(self, name):
        self._get_plugin(name).enable()

    def diable_plugin(self, name):
        self._get_plugin(name).disable()

