from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from datetime import datetime
from config import TIMEZONE


# TODO: make examples for docstrings

class AbstractPlugin(metaclass=ABCMeta):
    __slots__ = ("_enabled")
    _enabled: bool

    def __init__(self):
        _enabled = True

    @abstractmethod
    def user_commands(self) -> tuple[tuple[str, Callable], ...]:
        """Return sequence of user's command name and actions pairs.
        Action is usualy a plugin method.
        """
        ...

    @abstractmethod
    def plg_events(self) -> tuple[tuple[datetime, Callable]]:
        """Return sequence of time and action pairs.
        Action is usualy a plugin method.
        """
        ...

    def enable(self):
        """Enable plugin.
        Note: This method could be overrided in child class,
        but you shoud call `super().enable()` inside new method
        """
        self._enabled = True

    def disable(self):
        """Disable plugin.
        Note: This method could be overrided in child class,
        but you shoud call `super().enable()` inside new method
        """
        self._enabled = False

    @property
    def isenabled(self):
        """Shows is plugin enabled or not.
        Important note: by default, this does not affect the behavior
        of the plugin itself. The presence or absence of any actions
        depending on this property should be handled in other classes.
        """
        return self._enabled

    def _get_datetime_now(self) -> datetime:
        """Return current time"""
        return datetime.now(tz=TIMEZONE)