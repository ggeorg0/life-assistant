from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from datetime import datetime
from config import TIMEZONE


# TODO: make examples for docstrings

class AbstractPlugin(metaclass=ABCMeta):
    __slots__ = ("_enabled", "_name")
    _enabled: bool
    _name: str

    def __init__(self, name):
        self._enabled = True
        self._name = name

    @abstractmethod
    def user_commands(self) -> tuple[tuple[str, Callable], ...]:
        """Return sequence of user's command name and actions pairs.
        Action is usualy a plugin method.
        """
        ...

    @abstractmethod
    def daily_events(self) -> tuple[tuple[datetime, Callable]]:
        """Daily scheduled plugin events.

        Return sequence of time and action pairs
        (action is usualy a plugin method)
        """
        ...

    @abstractmethod
    def monthly_events(self) -> tuple[tuple[datetime, Callable]]:
        """Monthly scheduled plugin events.

        Return sequence of datetime and action pairs
        (action is usualy a plugin method).
        Note: `year` and `month` parts of the
        `datetime` will be ignored.
        """
        ...

    @abstractmethod
    def disordered_events(self) -> tuple[tuple[datetime, Callable]]:
        """Single plugin events, that can spawn other single events.
        Scheduled time of execution can be pretty chaotic,
        because it depends on the specific plugin.

        Return sequence of datetime and action pairs
        (action is usualy a plugin method).
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
        """Show is the plugin enabled or not.
        Important note: by default, this does not affect the behavior
        of the plugin itself. The presence or absence of any actions
        depending on this property should be handled in other classes.
        """
        return self._enabled

    @property
    def name(self):
        return self._name

    def _get_datetime_now(self) -> datetime:
        """Return current time"""
        return datetime.now(tz=TIMEZONE)