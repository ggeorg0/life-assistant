from typing import Any, Callable, Coroutine
from datetime import datetime

from extension import ActionResult


ActionT = Callable[..., Coroutine[Any, Any, ActionResult]]
EventsScheduleT = tuple[()] | tuple[tuple[datetime, ActionT], ...]
CommandBindingsT = tuple[()] | tuple[tuple[str, ActionT], ...]

