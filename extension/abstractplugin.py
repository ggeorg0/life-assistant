from abc import ABCMeta, abstractmethod
from datetime import datetime

from config import TIMEZONE
from extension.exttypes import EventsScheduleT, CommandBindingsT

class AbstractPlugin(metaclass=ABCMeta):
    """Abstract base class for your fancy plugin.
    """
    __slots__ = ("_enabled", "_name")
    _enabled: bool
    _name: str

    def __init__(self, name):
        self._enabled = True
        self._name = name

    @abstractmethod
    def user_commands(self) -> CommandBindingsT:
        """Return sequence of user's command name and actions pairs.

        Action should be a function defined with `async`
        and return instance of `ActionResult`.
        """
        ...

    @abstractmethod
    def daily_events(self) -> EventsScheduleT:
        """Daily scheduled plugin events.

        Return a sequence of pairs: `datetime`, action

        Action should be a function defined with `async`
        and return instance of `ActionResult
        """
        ...

    @abstractmethod
    def monthly_events(self) -> EventsScheduleT:
        """Monthly scheduled plugin events.

        Return a sequence of pairs: `datetime`, action.

        Action should be a function defined with `async`
        and return instance of `ActionResult.

        Note: `year` and `month` parts of the
        `datetime` will be ignored.
        """
        ...

    @abstractmethod
    def disordered_events(self) -> EventsScheduleT:
        """Single plugin events, that can spawn other single events.
        Scheduled time of execution can be pretty chaotic,
        because it depends on the specific plugin.

        Return a sequence of pairs: `datetime`, action.

        Action should be a function defined with `async`
        and return instance of `ActionResult.
        """
        ...

    @abstractmethod
    def help(self, *args) -> dict[str, tuple[str, ...]]:
        """
        Return `dict` of command descriptions with their aliases.

        Example of `help`:
        ```
        def help:
            return {
                "this command do a very cool action":
                    ('/command <param1> <param2>', '/commandalias'),
                "another command's description":
                    ('/anothercommand', )
            }
        ```
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
        Important note: The presence or absence of any actions
        depending on this property handled in other classes.
        """
        return self._enabled

    @property
    def name(self):
        return self._name

    def _get_datetime_now(self) -> datetime:
        """Return current time"""
        return datetime.now(tz=TIMEZONE)



