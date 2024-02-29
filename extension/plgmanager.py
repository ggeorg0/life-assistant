from itertools import count
import logging
from collections.abc import Callable, Iterable
from datetime import datetime

from extension import AbstractPlugin, ActionResult


class PluginManager(AbstractPlugin):
    """
    Manage loaded plugins.
    Note: This class is inherited from `AbstractPlugin`
    because the user needs to manage plugins with commands like
        `/enable <PluginName>`
        `/disable <PluginName>`
        `/plugins` ... \n
    and `ExtensionLoader` wants to get `AbstractPlugin`
    instances to add new commands to the bot.
    """
    # Singletone class
    _ids = count(0)
    _loaded_plugins: dict[str, AbstractPlugin]

    def __init__(self, plugins: Iterable[AbstractPlugin] = []):
        self.id = next(self._ids)
        if self.id > 1:
            raise RuntimeError("There are additional PluginManager instance")
        super().__init__('PluginManager')
        self.set_plugins(plugins)

    def user_commands(self) -> Iterable[tuple[AbstractPlugin, str, Callable]]:
        logging.info("Plugin Manager: loading user commands")
        for p in self._loaded_plugins.values():
            if p.isenabled:
                for command, action in p.user_commands():
                    yield (p, command, action)
            else:
                logging.info(f"Plugin Manager: skipping [{p.name}]"
                             " (not enabled)")
        for command, action in self._manage_commands():
            yield (self, command, action)

    def _manage_commands(self) -> Iterable[tuple[str, Callable]]:
        return (
            ("enable", self.enable_plugin),
            ("disable", self.disable_plugin),
            ("plugins", self.list_plugins),
            ("pl", self.list_plugins)
        )

    def daily_events(self) -> Iterable[tuple[AbstractPlugin, datetime, Callable]]:
        logging.info("Plugin Manager: loading daily events")
        for p in self._loaded_plugins.values():
            if p.isenabled:
                for dt, action in p.daily_events():
                    yield (p, dt, action)
            else:
                logging.info(f"Plugin Manager: skipping [{p.name}]"
                             " (not enabled)")

    def monthly_events(self) -> Iterable[tuple[AbstractPlugin, datetime, Callable]]:
        logging.info("Plugin Manager: loading monthly events")
        for p in self._loaded_plugins.values():
            if p.isenabled:
                for dt, action in p.monthly_events():
                    yield (p, dt, action)
            else:
                logging.info(f"Plugin Manager: skipping [{p.name}]"
                             " (not enabled)")

    def disordered_events(self) -> Iterable[tuple[AbstractPlugin, datetime, Callable]]:
        logging.info("Plugin Manager: loading disordered events")
        for p in self._loaded_plugins.values():
            if p.isenabled:
                for dt, action in p.disordered_events():
                    yield (p, dt, action)
            else:
                logging.info(f"Plugin Manager: skipping [{p.name}]"
                             " (not enabled)")

    def set_plugins(self, plugins: Iterable[AbstractPlugin]):
        self._loaded_plugins = {p.name: p for p in plugins}

    def _get_plugin(self, name):
        return self._loaded_plugins[name]

    async def enable_plugin(self, *args):
        """User command for enabling plugin by name (args)"""
        return self._switch_plugin(self._enable_plugin, *args)

    async def disable_plugin(self, *args):
        """User command for disabling plugin by name (args)"""
        return self._switch_plugin(self._diable_plugin, *args)

    def _switch_plugin(self, switcher: Callable, *args):
        """Wrapper for _enable and _disable methods"""
        try:
            plugin_name = " ".join(args)
            return switcher(plugin_name)
        except (IndexError, KeyError):
                return ActionResult(
                    "Error: you must specify correct plugin name\n"
                    "Hint: use /plugins to see loaded plugins"
                )

    def _enable_plugin(self, name) -> ActionResult:
        self._get_plugin(name).enable()
        return ActionResult(f"[{name}] is enabled now")

    def _diable_plugin(self, name):
        if name == self.name:
            return ActionResult("You cannot turn off PluginManager")
        self._get_plugin(name).disable()
        return ActionResult(f"[{name}] is disabled now")

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

    def disable(self):
        logging.error("It is not possible to disable the PluginManager")

    def help(self):
        # TODO!!!
        ...

