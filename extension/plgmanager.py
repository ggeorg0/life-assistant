from itertools import count
import logging
from collections.abc import Callable, Iterable
from datetime import datetime

from extension import AbstractPlugin, ActionResult


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

    def manage_commands(self) -> Iterable[tuple[str, Callable]]:
        return (
            ("enable", self.enable_plugin),
            ("disable", self.disable_plugin),
            ("plugins", self.list_plugins),
            ("pl", self.list_plugins)
        )

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

    async def enable_plugin(self, *args):
        """User command for enabling plugin by name (args)"""
        return self._switch_plugin(self._enable_plugin, "enabled now", *args)

    async def disable_plugin(self, *args):
        """User command for disabling plugin by name (args)"""
        return self._switch_plugin(self._diable_plugin, "disabled now", *args)

    def _switch_plugin(self, switcher, success_message: str, *args):
        """Wrapper for _enable and _disable methods"""
        try:
            plugin_name = " ".join(args)
            switcher(plugin_name)
            return ActionResult(f"[{plugin_name}] is {success_message}")
        except (IndexError, KeyError):
                return ActionResult(
                    "Error: you must specify correct plugin name\n"
                    "Hint: use /plugins to see loaded plugins"
                )

    async def list_plugins(self) -> ActionResult:
        """User command for listing loaded plugins"""
        message = ['<pre>']     # <pre> - HTML formatting of code
        message.append(f"{'Plugin Name':20} {'Enabled':7}")
        message.append('-' * 29)
        for name, plg in self._loaded_plugins.items():
            enabled = 'YES' if plg.isenabled else 'NO'
            message.append(f"{name:20} {enabled:>7}")
        message.append('</pre>')
        return ActionResult('\n'.join(message))

    def _enable_plugin(self, name):
        self._get_plugin(name).enable()

    def _diable_plugin(self, name):
        self._get_plugin(name).disable()

