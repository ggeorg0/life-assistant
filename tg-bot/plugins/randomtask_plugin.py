from random import choice
from .interface import AbstractPlugin, ActionsCallbackTuple
from tools import protect_for_html
from notion import Notion

class RandomCurrentTask(AbstractPlugin):
    
    # page_id of last chosen taks
    _last_task_id: str | None
    _last_task_name: str
    _last_created_in_done: str | None
    
    def __init__(self, name="RandomCurrentTask") -> None:
        super().__init__(name)
        self._last_task_id = None
        self._notion = Notion()
    
    async def random_current_task(self, *args):
        tasks = await self._notion.current_tasks()
        task_id, task_title = choice(list(tasks.items()))
        self._last_task_id = task_id
        self._last_task_name = task_title
        return protect_for_html(task_title)
    
    async def complete_last_task(self, *args):
        if self._last_task_id:
            self._last_created_in_done = await \
                self._notion.move_to_done(self._last_task_id)
            return f"The task \"{self._last_task_name}\" is marked as completed!"
        else:
            return "There are no last task!"
    
    async def doagain_last_task(self, *args):
        if self._last_task_id:
            await self._notion.unarchive_page(self._last_task_id)
            if self._last_created_in_done:
                await self._notion.archive_page(self._last_created_in_done)
            return "The task is back!"
        else:
            return "There are no last task!"
        
    @property
    def message_callabacks(self) -> tuple[ActionsCallbackTuple, ...]:
        return ()
    
    @property
    def actions_callbacks(self) -> tuple[ActionsCallbackTuple, ...]:
        return ()
    

plg = RandomCurrentTask
