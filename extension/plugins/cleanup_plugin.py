from datetime import date, datetime

from extension import AbstractPlugin, ActionResult
from extension.exttypes import CommandBindingsT, EventsScheduleT
from mynotion import Notion

from config import TIMEZONE

class CalenarCleanupPlugin(AbstractPlugin):
    __slots__ = (
        "_notion",
    )

    def __init__(self) -> None:
        super().__init__(name="CalenarCleanup")
        self._notion = Notion()

    async def remove_past_events(self, *args) -> ActionResult:
        events = await self._notion.get_calendar_events()
        today = datetime.now(TIMEZONE).date()
        deleted = 0
        for ev in events:
            if self._is_event_passed(ev, today):
                await self._notion.archive_page(ev['id'])
                deleted += 1
        return ActionResult(
            message=f"{deleted} past events have been deleted!"
        )
        
    @staticmethod
    def _is_event_passed(event: dict, today: date): 
        return (
            event['end'] and event['end'].date() < today 
                or (not event['end'] and event['start'].date() < today)
        )

    def user_commands(self) -> CommandBindingsT:
        return (
            ("rm_past_events", self.remove_past_events),
        )

    def help(self, *args) -> dict[str, tuple[str, ...]]:
        return {
            "Remove past events from calendar":
                ('/rm_past_events', ),
        }

    def daily_events(self) -> EventsScheduleT:
        return ()

    def monthly_events(self) -> EventsScheduleT:
        return ()

    def disordered_events(self) -> EventsScheduleT:
        return ()

