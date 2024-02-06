from dataclasses import dataclass
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from collections.abc import Callable

@dataclass
class ActionResult:
    message: str
    next_datetime: datetime
    next_action: Callable
