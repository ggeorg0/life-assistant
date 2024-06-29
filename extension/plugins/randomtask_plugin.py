from collections.abc import Callable
from datetime import datetime
from random import choice
from typing import Any

from extension import AbstractPlugin, ActionResult
from extension.exttypes import ActionT, CommandBindingsT, EventsScheduleT
from tools import protect_for_html
from mynotion import Notion


class RandomCurrentTask(AbstractPlugin):
    __slots__ = (
        "_last_task_id",
        "_last_task_name",
        "_notion"
    )
    # page_id of last chosen taks
    _last_task_id: str | None
    _last_task_name: str

    def __init__(self) -> None:
        super().__init__(name="RandomCurrentTask")
        self._last_task_id = None
        self._notion = Notion()

    async def random_current_task(self, *args) -> ActionResult:
        tasks = await self._notion.get_current_tasks()
        task_id, task_title = choice(tuple(tasks.items()))
        self._last_task_id = task_id
        self._last_task_name = task_title
        return ActionResult(
            message=protect_for_html(task_title)
        )

    async def complete_last_task(self, *args) -> ActionResult:
        if self._last_task_id:
            await self._notion.archive_page(self._last_task_id)
            message = f"The task \"{self._last_task_name}\" is archived!"
        else:
            message = "There are no last random task!"
        return ActionResult(
            message=protect_for_html(message)
        )

    async def doagain_last_task(self, *args) -> ActionResult:
        if self._last_task_id:
            await self._notion.unarchive_page(self._last_task_id)
            message = "The task is back!"
        else:
            message = "There are no last random task!"
        return ActionResult(message=message)

    def user_commands(self) -> CommandBindingsT:
        return (
            ("rtask", self.random_current_task),
            ("task", self.random_current_task),
            ("done", self.complete_last_task),
            ("undone", self.doagain_last_task)
        )

    def help(self, *args) -> dict[str, tuple[str, ...]]:
        return {
            "Random task from `Current Tasks` notion list":
                ('/rtask', '/task'),
            "Mark as complete last random task":
                ('/done', ),
            "Мark as incomplete last random task":
                ('/undone', ),
        }

    def daily_events(self) -> EventsScheduleT:
        return ()

    def monthly_events(self) -> EventsScheduleT:
        return ()

    def disordered_events(self) -> EventsScheduleT:
        return ()

plg = RandomCurrentTask
