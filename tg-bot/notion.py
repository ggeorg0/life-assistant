from datetime import datetime

from notion_client import AsyncClient, APIErrorCode, APIResponseError
from notion_client.helpers import async_iterate_paginated_api, is_full_page

from config import BOT_TOKEN, INTEGRATION_TOKEN
from config import TG_TARGET_ID, INBOX_DATABASE_ID
from config import CALENDAR_DATABASE_ID
from config import CURRENT_TASKS_ID
from config import DEPTH_LIMIT, PAGE_SIZE
from config import PAIR_SCHEDULE, UNI_SCHEDULE

from tools import protect_for_html, singleton


@singleton
class Notion():
    _client: AsyncClient

    def __init__(self) -> None:
        self._client = AsyncClient(auth=INTEGRATION_TOKEN)

    async def create_page_in_inbox(self, title: str):
        return await self._client.pages.create(
            parent={'database_id': INBOX_DATABASE_ID},
            properties={
                'Name': {
                'title': [{'text': {'content': title}}]
            }, 
        })
    
    async def last_inbox_pages(self) -> list[str]:
        results = await self._client.databases.query(database_id=INBOX_DATABASE_ID,
                                                     sorts=[{"property": "Created",
                                                             "direction": "descending"}],
                                                     page_size=PAGE_SIZE)
        titles = ["<b>List of tasks</b>"]
        for i, task in enumerate(results["results"]):
            if is_full_page(task):
                task_title = task["properties"]["Name"]["title"]
                if task_title:
                    line = f"{i + 1}. {task_title[0]['plain_text']}"
                    titles.append(protect_for_html(line))
        if results["next_cursor"] != None:
            titles.append("<b>Visit Notion to see full list...</b>")
        return titles

    async def archive_n_pages(self, count=1):
        results = await self._client.databases.query(database_id=INBOX_DATABASE_ID, 
                                                     sorts=[{"property": "Created",
                                                             "direction": "descending"}],
                                                     page_size=count)
        for p in results["results"]:
            await self._client.pages.update(page_id=p['id'], archived=True)
    
    async def today_calendar_events(self):
        events = []
        async for block in async_iterate_paginated_api(
            self._client.databases.query, database_id=CALENDAR_DATABASE_ID
        ):
            for p in block:
                event = {}
                props = p["properties"]
                if props["Name"]["title"]:
                    event['title'] = props["Name"]["title"][0]['plain_text']
                    date = props["Date"]['date']
                    if date:
                        event['start'] = datetime.fromisoformat(date['start'])
                        event['end'] = date['end']
                        if event['end']:
                            event['end'] = datetime.fromisoformat(event['end'])
                        events.append(event)
        return events
    
    async def current_tasks(self):
        tasks = []
        async for block in async_iterate_paginated_api(
            self._client.databases.query, database_id=CURRENT_TASKS_ID
        ):
            for p in block:
                props = p["properties"]
                if props["Name"]["title"]:
                    tasks.append( props["Name"]["title"][0]['plain_text'])
        return tasks
    
    async def uni_schedule(self): 
        results = self._client.databases.query(database_id=UNI_SCHEDULE)
        weekday = datetime.today().weekday()
        daily_schedule = []
        for p in results:
            props = p['results']
            page_weekday = int(props['День недели']['select']['name'])

            pair_num = props['Пара']['number']
            subject = props['Предмет']['title'][0]['plain_text']
            lecturer = props['Преподаватель']['rich_text'][0]['plain_text']

            if page_weekday-1 == weekday:
                daily_schedule.append([pair_num, PAIR_SCHEDULE[pair_num],
                                       subject, lecturer])