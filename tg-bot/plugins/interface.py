from abc import ABCMeta, abstractmethod, abstractproperty
from typing import Sequence, Callable, Awaitable, Any 
from datetime import datetime

MessageCallbackTuple = tuple[datetime, Callable[..., Awaitable[str]], str]
ActionsCallbackTuple = tuple[datetime, Callable[..., Awaitable[Any]], str]

# depricated
# TODO: delete this class later
class MorningMsgPlugin(metaclass=ABCMeta):
    _enabled: bool
    _name: str

    def __init__(self) -> None:
        self._enabled = True
        self._name = "defaultpluginname"

    def process_message(self, message: list[str]):
        if self.enabled:
            return self._process_message(message)

    @abstractmethod
    def _process_message(self, message: list[str]):
        raise NotImplementedError("Subclasses must implement this method")
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value


class AbstractPlugin(metaclass=ABCMeta):
    _enabled: bool
    _name: str

    def __init__(self, name="defaultname") -> None:
        self._enabled = True
        self._name = name

    @abstractproperty
    def message_callabacks(self) -> tuple[ActionsCallbackTuple, ...]:
        raise NotImplementedError

    @abstractproperty
    def actions_callbacks(self) -> tuple[ActionsCallbackTuple, ...]:
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

