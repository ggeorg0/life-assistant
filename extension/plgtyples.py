from typing import Any, Callable, Coroutine
from datetime import datetime

from extension import ActionResult


ActionT = Callable[..., Coroutine[Any, Any, ActionResult]]
EventsScheduleT = tuple[tuple[datetime, ActionT], ...]  | tuple[()]
CommandBindingsT = tuple[tuple[str, ActionT], ...] | tuple[()]

