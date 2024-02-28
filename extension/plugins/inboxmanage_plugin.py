import logging

from extension import AbstractPlugin, ActionResult
from extension.exttypes import CommandBindingsT, EventsScheduleT
from notion import Notion
# from tools import protect_for_html
from config import (
    INBOX_LAST_N
)

class InboxManagement(AbstractPlugin):
    __slots__ = (
        "_notion",
    )
    _notion: Notion

    def __init__(self):
        super().__init__("Inbox Management")
        self._notion = Notion()

    def user_commands(self) -> CommandBindingsT:
        return (
            ("delete_last", self.delete_last_n),
            ("delete", self.delete_last_n),
            ("del_last", self.delete_last_n),
            ("inbox", self.last_tasks)
        )

    async def last_tasks(self, *args) -> ActionResult:
        # TODO: move code from `_notion.last_inbox_pages` here
        if len(args) < 1:
            tasks_number = INBOX_LAST_N
        else:
            tasks_number = int(args[0])
        titles = await self._notion.last_inbox_pages(tasks_number)
        #   it is already in `_notion.last_inbox_pages`, wich is not good:
        # titles = map(protect_for_html, titles) --
        return ActionResult("\n".join(titles))

    async def delete_last_n(self, *args) -> ActionResult:
        if len(args) < 1:
            return ActionResult("Error: you must specify number of pages."
                                "Example \n"
                                "<pre>delete_last 10 </pre>")
        try:
            n = int(args[0])
            await self._notion.archive_n_pages(n)
            return ActionResult(f"{n} pages have been deleted")
        except ValueError:
            return ActionResult(f"Invalid number of pages: {args[0]}")
        except Exception as e:
            logging.error(f"[Inbox Managenet]: {e}")
            return ActionResult(f"Some error occured during deletion")


    def daily_events(self) -> EventsScheduleT:
        return ()

    def monthly_events(self) -> EventsScheduleT:
        return ()

    def disordered_events(self) -> EventsScheduleT:
        return ()
