import os
import importlib
from itertools import count, chain
import logging
from typing import Generator, Any

from .interface import MorningMsgPlugin, AbstractPlugin


class PluginManager:
    _ids = count(0)
    _loaded_plugins: dict[str, AbstractPlugin]
    def __init__(self, plugin_directory: str) -> None:
        self.id = next(self._ids)
        if self.id > 1:
            raise RuntimeError("There are additional PluginManager instance")
        self.plugin_directory = plugin_directory

    def load_plugins(self):
        plugins = {}
        for plugin_file in os.listdir(self.plugin_directory):
            if plugin_file.endswith("plugin.py"):
                plugin_name = os.path.splitext(plugin_file)[0]
                plugin_module = importlib.import_module(f"{'plugins'}.{plugin_name}")
                plugin_instance = plugin_module.plg()
                plugins[plugin_instance.name] = plugin_instance
        self._loaded_plugins = plugins
        return self
    
    @property
    def loaded_plugins(self) -> Generator[AbstractPlugin, None, None]:
        return (p for k, p in self._loaded_plugins.items() if p.enabled)
    
    def get_enabled_plugin(self, plg_name: str) -> AbstractPlugin | None:
        if (plg_name in self._loaded_plugins 
                and self._loaded_plugins[plg_name].enabled):
            return self._loaded_plugins[plg_name]
        return None
    
    def _get_plugin(self, plg_name):
        return self._loaded_plugins[plg_name]

    def turn_off_plugin(self, name):
        self._get_plugin(name).enabled = False

    def turn_on_plugin(self, name):
        self._get_plugin(name).enabled = True
            
    def plugins_messages(self) -> tuple:
        return tuple(chain.from_iterable(p.message_callabacks 
                                         for p in self.loaded_plugins))
    
    def plugin_actions(self) -> tuple:
        return tuple(chain.from_iterable(p.actions_callbacks 
                                         for p in self.loaded_plugins))



            

