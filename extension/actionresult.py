from dataclasses import dataclass
from datetime import datetime
from collections.abc import Callable

@dataclass
class ActionResult:
    message: str | None = None
    next_datetime: datetime | None = None
    next_action: Callable | None = None
