from collections.abc import Iterable
from itertools import count
import logging

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

    def user_commands(self):
        # return ("commandname", action), ...
        # TODO
        pass

    def scheduled_events(self):
        # return (datetime, action), ...
        # TODO
        pass

    def set_plugins(self, plugins: Iterable[AbstractPlugin]):
        self._loaded_plugins = {p.name: p for p in plugins}

    def _get_plugin(self, name):
        return self._loaded_plugins[name]

    def enable_plugin(self, name):
        self._get_plugin(name).enable()

    def diable_plugin(self, name):
        self._get_plugin(name).disable()

