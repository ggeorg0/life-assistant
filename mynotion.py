from datetime import datetime, date
from typing import Sequence

from notion_client import AsyncClient, APIErrorCode, APIResponseError
from notion_client.helpers import async_iterate_paginated_api, is_full_page

from config import (
    INTEGRATION_TOKEN,
    INBOX_DATABASE_ID,
    DONE_LIST_ID,
    CALENDAR_DATABASE_ID,
    CURRENT_TASKS_ID,
    PAIR_SCHEDULE,
    UNI_SCHEDULE,
    WEEKDAYS
)

from tools import singleton

PairTime = tuple[int, tuple[int, int], tuple[int, int]]
PairProperties = tuple[int, PairTime, str, str, str]

@singleton
class Notion():
    _client: AsyncClient

    def __init__(self) -> None:
        self._client = AsyncClient(auth=INTEGRATION_TOKEN)

    async def create_page_in_inbox(self, title: str):
        return await self._client.pages.create(
            parent={'database_id': INBOX_DATABASE_ID},
            properties={
                'Name': {'title': [{'text': {'content': title}}]}
            })

    async def last_inbox_pages(self, n_pages: int) -> list[str]:
        results = await self._client.databases.query(
            database_id=INBOX_DATABASE_ID,
            sorts=[{"property": "Created",
                    "direction": "descending"}],
            page_size=n_pages
        )
        titles = []
        for i, task in enumerate(results["results"]):
            if is_full_page(task):
                task_title = task["properties"]["Name"]["title"]
                if task_title:
                    line = f"{i+1:>3d}. {task_title[0]['plain_text']}"
                    titles.append(line)
        if results["next_cursor"] != None:
            titles.append("Visit Notion to see full list...")
        return titles

    async def archive_n_pages(self, count=1):
        results = await self._client.databases.query(database_id=INBOX_DATABASE_ID,
                                                     sorts=[{"property": "Created",
                                                             "direction": "descending"}],
                                                     page_size=count)
        for p in results["results"]:
            await self.archive_page(id=p['id'])

    async def archive_page(self, id: str):
        await self._client.pages.update(page_id=id, archived=True)

    async def unarchive_page(self, id: str):
        await self._client.pages.update(page_id=id, archived=False)

    async def move_to_done(self, id: str):
        """Actually, this method archives page
        and creates it's copy in Done list"""
        done_props = await self._client.pages.retrieve(id)
        new_page = await self._client.pages.create(
            parent={'database_id': DONE_LIST_ID},
            properties=done_props['properties'])
        await self.archive_page(id)
        return new_page['id']

    async def today_calendar_events(self):
        events = []
        async for page in async_iterate_paginated_api(
            self._client.databases.query,
            database_id=CALENDAR_DATABASE_ID
        ):
            event = {}
            props = page["properties"]
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

    async def current_tasks(self) -> dict[str, str]:
        tasks = {}
        async for page in async_iterate_paginated_api(
            self._client.databases.query, database_id=CURRENT_TASKS_ID
        ):
            props = page["properties"]
            id = page['id']
            if props["Name"]["title"]:
                task_title = props["Name"]["title"][0]['plain_text']
                tasks[id] = task_title
        return tasks


    async def uni_daily_schedule(self, day: date) -> Sequence[PairProperties]:
        results = await self._client.databases.query(database_id=UNI_SCHEDULE)
        weekday = day.weekday()
        daily_schedule = []
        for p in results['results']:
            props = p['properties']
            page_weekday = props['День недели']['select']['name']
            page_weekday = WEEKDAYS[page_weekday]

            pair_num = int(props['Пара']['number'])
            subject = props['Предмет']['title'][0]['plain_text']
            lecturer = props['Преподаватель']['rich_text'][0]['plain_text']
            auditory = props['Кабинет']['rich_text'][0]['plain_text']

            if page_weekday-1 == weekday:
                daily_schedule.append( (pair_num, PAIR_SCHEDULE[pair_num - 1],
                                       subject, lecturer, auditory) )
        return daily_schedule
