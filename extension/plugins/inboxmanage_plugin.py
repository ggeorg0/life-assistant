import logging

from extension import AbstractPlugin, ActionResult
from extension.exttypes import CommandBindingsT, EventsScheduleT
from mynotion import Notion
from tools import protect_for_html
from config import INBOX_LAST_N

class InboxManagement(AbstractPlugin):
    __slots__ = (
        "_notion",
    )
    _notion: Notion

    def __init__(self):
        super().__init__("InboxManagement")
        self._notion = Notion()

    def user_commands(self) -> CommandBindingsT:
        return (
            ("delete_last", self.delete_last_n),
            ("delete", self.delete_last_n),
            ("del_last", self.delete_last_n),
            ("inbox", self.last_tasks),
            ("last", self.last_tasks)
        )

    async def last_tasks(self, *args) -> ActionResult:
        try:
            tasks_number = int(args[0])
        except (ValueError, IndexError):
            tasks_number = INBOX_LAST_N
        titles = await self._notion.last_inbox_pages(tasks_number)
        titles = list(map(protect_for_html, titles))
        message = ["<b>List of tasks</b>"] + titles
        return ActionResult("\n".join(message))

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

    def help(self, *args) -> dict[str, tuple[str, ...]]:
        return {
            "delete last N tasks from inbox":
                ('/delete <n>', '/delete_last <n>', '/del_last <n>'),
            "show last N (default is 10) tasks in inbox":
                ('/inbox [n]', '/last [n]'),
        }

    def daily_events(self) -> EventsScheduleT:
        return ()

    def monthly_events(self) -> EventsScheduleT:
        return ()

    def disordered_events(self) -> EventsScheduleT:
        return ()
