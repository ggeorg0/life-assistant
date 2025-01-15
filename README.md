# Life Assistant Bot

Life Assistant Bot is a Telegram bot designed to help me manage my daily tasks, calendar events, and other activities using Notion. You can copy and modify the code of this project to suit your needs.

## Motivation
From my experience, the Notion mobile app works badly without an internet connection: if you try to add anything to your collections or edit some items, the information sometimes gets completely wiped out. The app is also very slow. As a result, it is very frustrating to even touch Notion on mobile.

On the other hand, Telegram allows you to send messages if you are offline. The app will try to resend them multiple times until the connection is restored. And the bot uses this advantage.

Furthermore, if you are adding some tasks through the bot and the Notion service is offline for some reason, the bot will try to resend the information later (with increasing time between retries). This significantly increases the chances for your data to be safely delivered.

In addition, the bot offers extra features such as sending a daily summary of current tasks every morning and providing the university schedule.

**⚠️ This project is archived because I no longer use Notion.**  

## Features

- **Task Management**: Add tasks to your Notion inbox directly from Telegram.
- **Plugin System**: Extend the bot's functionality with plugins. Almost all the functionality is implemented through plugins. And you don't even need to know how telegram API works.
- **Daily and Monthly Events**: Schedule daily and monthly events using plugins. 

<div align="center">
    <img src="https://github.com/user-attachments/assets/54f4c77a-ae69-464f-9564-48d957a0de23"  width="360" >
</div>

## Getting Started

### Prerequisites

- Python 3.8+
- Notion inegration token
- Telegram bot token

In the Notion I have next databases:
- Inbox
- Calendar
- Current tasks
- University schedule

In the Notion you need to add your bot ("connection") for each database. 

And you also need to add database ids in the `.env` file.

### Installation

1. Clone the repository:

```sh
git clone https://github.com/ggeorg0/life-assistant.git
cd life-assistant
```

2. Install the required dependencies:

```sh
pip install -r requirements.txt
```

3. Fill in the `.env` with its own notion/telegram tokens

### Usage

Run the bot using the following command:

```sh
python bot.py
```

Send **any text message** to the bot to **add it as a task to your Notion inbox**. Any arbitrary text message will be threated like task.

For other cases use `/help` to see the list of available commands from all plugins

<div align="center">
    <img src="https://github.com/user-attachments/assets/7cd01ab9-3249-4424-b371-8ec8b3a8a377"  width="360">
</div>

## Plugin System

The Life Assistant Bot features a flexible plugin system that allows you to extend its functionality. Plugins can define multiple user commands, daily events, monthly events, and single events. 

Moreover, each event or user command could spawn other single/daily/monthly events.

### Plugins available by default  

Here are some of the available plugins:

- **Cleanup Plugin**: Remove past events from your calendar.
- **Inbox Management Plugin**: Manage your Notion inbox.
- **Morning Summary Plugin**: Get a morning summary of your tasks and events.
- **Random Task Plugin**: Get a random task from your current tasks.
- **Timer Plugin**: Set timers and get notifications when they expire.
- **Uni Schedule Plugin**: Manage your university schedule.

You can delete or modify each of these plugins without breaking the bot.

### Adding a new plugin

Each plugin is a Python class that inherits from the `AbstractPlugin` class defined in `extension/abstractplugin.py`

A plugin must implement the following abstract methods:
- `user_commands`: Defines user commands like `/command` and corresponding actions.
- `daily_events`: Defines daily scheduled events.
- `monthly_events`: Defines monthly scheduled events.
- `disordered_events`: Defines single events that can spawn other single events.
- `help`: Provides help information for the plugin's commands, which is accessible via `/help`

The plugin filename must end with `_plugin.py` and stored in `extension/plugins/` directory.

### Plugin example

Here is an example of a simple plugin that removes past events from the calendar:

```python
from datetime import date, datetime

from extension import AbstractPlugin, ActionResult
from extension.exttypes import CommandBindingsT, EventsScheduleT
from mynotion import Notion

from config import TIMEZONE

class CalendarCleanupPlugin(AbstractPlugin):
    def __init__(self) -> None:
        super().__init__(name="CalendarCleanup")
        self._notion = Notion()

    async def remove_past_events(self, *args) -> ActionResult:
        events = await self._notion.get_calendar_events()
        today = datetime.now(TIMEZONE).date()
        deleted = 0
        for ev in events:
            if self._is_event_passed(ev, today):
                await self._notion.archive_page(ev['id'])
                deleted += 1
        # plugin action must return ActionResult
        return ActionResult(
            message=f"{deleted} past events have been deleted!"
        )
        
    def _is_event_passed(event: dict, today: date): 
        return (
            event['end'] and event['end'].date() < today 
                or (not event['end'] and event['start'].date() < today)
        )

    def user_commands(self) -> CommandBindingsT:
        return (
            ("rm_past_events", self.remove_past_events),
        )

    def help(self, *args):
        return {
            "Remove past events from calendar":
                ('/rm_past_events', ),
        }

    def daily_events(self) -> EventsScheduleT:
        # no daily events
        return ()

    def monthly_events(self) -> EventsScheduleT:
        # no monthly events
        return ()

    def disordered_events(self) -> EventsScheduleT:
        # no single events
        return ()
```

## Project Structure

If you want to customize the bot beyond plugins, you can modify the core logic. Here the project structure to help you:

```
life-assistant
├── bot.py      # the main bot file 
├── config.py   # config file values loaded from "./.env" by default
├── extension/      # code for plugins and plugins itself
│   ├── __init__.py
│   ├── abstractplugin.py   # abstract class for all user-defined plugins 
│   ├── actionresult.py
│   ├── extensionloader.py
│   ├── exttypes.py
│   ├── plgloader.py
│   ├── plgmanager.py
│   └── plugins/        # user-defined plugins 
│       ├── cleanup_plugin.py
│       ├── inboxmanage_plugin.py
│       ├── moriningsummary_plugin.py
│       ├── randomtask_plugin.py
│       ├── timer_plugin.py
│       └── uni_schedule_plugin.py
├── mynotion.py     # notion integrations
├── README.MD       
├── requirements.txt
└── tools.py
```

## Acknowledgements

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [notion-client](https://github.com/ramnes/notion-sdk-py)
- [dotenv](https://github.com/theskumar/python-dotenv)
