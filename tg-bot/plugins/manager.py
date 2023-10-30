import os
import importlib
from itertools import count
import logging

from .interface import MorningMsgPlugin

class PluginManager:
    _ids = count(0)
    _loaded_plugins: dict[MorningMsgPlugin, str]
    def __init__(self, plugin_directory: str) -> None:
        self.id = next(self._ids)
        if self.id > 1:
            raise RuntimeError("There are additional PluginManager instance")
        self.plugin_directory = plugin_directory

    def load_plugins(self):
        plugins = []
        for plugin_file in os.listdir(self.plugin_directory):
            if plugin_file.endswith("plugin.py"):
                plugin_name = os.path.splitext(plugin_file)[0]
                plugin_module = importlib.import_module(f"{'plugins'}.{plugin_name}")
                plugin_class = plugin_module.plg
                plugins.append(plugin_class())
        self._loaded_plugins = plugins
        return self

    def plugins_apply(self, data: list[str]):
        for plugin in self._loaded_plugins:
            if plugin.enabled:
                try:
                    plugin.process_message(data)
                except Exception as err:
                    logging.error(err)

    def turn_off_plugin(self, name):
        for plugin in self._loaded_plugins:
            if plugin.name == name:
                plugin.enabled = False
                break
        else:
            raise ValueError(f"Plugin with name {name} not found!")
        
        
            
