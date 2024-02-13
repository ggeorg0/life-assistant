import logging
import importlib.util
from inspect import isclass
from pathlib import Path
import traceback
import os

from extension import AbstractPlugin


class PluginLoader:
    __slots__ = (
        "_plugins_dir",
    )
    _plugins_dir: str

    def __init__(self, plugins_dir: str):
        self._plugins_dir = plugins_dir

    def load(self) -> list[AbstractPlugin]:
        plugin_files = [file for file in os.listdir(self._plugins_dir)
                        if file.endswith('plugin.py')]
        plugins = []
        for pf in plugin_files:
            try:
                plugins += self._load_plugin_file(pf)
            except Exception as e:
                logging.error(f"cannot load file `{pf}`, reason:\n"
                              f"{''.join(traceback.format_exception(e))}")
        return plugins

    def _load_plugin_file(self, filename) -> list[AbstractPlugin]:
            path, name = self._module_path_name(self._plugins_dir, filename)
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
