from random import choice
from .interface import AbstractPlugin, ActionsCallbackTuple
from tools import protect_for_html
from notion import Notion

class RandomCurrentTask(AbstractPlugin):
    
    # page_id of last chosen taks
    _last_task: str | None
    
    def __init__(self, name="RandomCurrentTask") -> None:
        super().__init__(name)
        self._last_task = None
        self._notion = Notion()
    
    async def random_current_task(self, *args):
        tasks = await self._notion.current_tasks()
        task_id, task_title = choice(list(tasks.items()))
        self._last_task = task_id
        return protect_for_html(task_title)
    
    async def archive_last_task(self, *args):
        if self._last_task:
            await self._notion.archive_page(self._last_task)
            return "The task is marked as completed!"
        else:
            return "There are no last task!"
    
    async def unarchive_last_task(self, *args):
        if self._last_task:
            await self._notion.unarchive_page(self._last_task)
            return "The task is back. Oops!"
        else:
            return "There are no last task!"
        
    @property
    def message_callabacks(self) -> tuple[ActionsCallbackTuple, ...]:
        return ()
    
    @property
    def actions_callbacks(self) -> tuple[ActionsCallbackTuple, ...]:
        return ()
    

plg = RandomCurrentTask
