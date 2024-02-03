import os
from datetime import time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# load environmental variables
def load_env_var(var_name: str) -> str:
    if value := os.environ.get(var_name):
        return value
    raise ValueError(f"{var_name} is not loaded properly")

load_dotenv(override=True)

# set applicatoin timezone
TIMEZONE = ZoneInfo("Europe/Moscow")

# telegram token and target user id
BOT_TOKEN = load_env_var("BOT_TOKEN")
TG_TARGET_ID = int(load_env_var("TG_TARGET_ID"))

# notion token
INTEGRATION_TOKEN = load_env_var("INTEGRATION_TOKEN")

# notion databases ids
INBOX_DATABASE_ID = load_env_var("INBOX_DATABASE_ID")
CALENDAR_DATABASE_ID = load_env_var("CALENDAR_DATABASE_ID")
CURRENT_TASKS_ID = load_env_var("CURRENT_TASKS_ID")
#TODO: rename UNI_SCHEDULE to UNI_SCHEDULE_ID
UNI_SCHEDULE = load_env_var("UNI_SCHEDULE")
DONE_LIST_ID = load_env_var("DONE_LIST_ID")

# other hyperparameters
DEPTH_LIMIT = 16
PAGE_SIZE = 25

PAIR_SCHEDULE = [[1, (9, 00), (10, 30)],
                 [2, (10, 40), (12, 10)],
                 [3, (12, 50), (14, 20)],
                 [4, (14, 30), (16, 00)],
                 [5, (16, 10), (17, 40)],
                 [6, (17, 50), (19, 20)]]

WEEKDAYS = {"Пн": 1, "Вт": 2, "Ср": 3, "Чт": 4, "Пт": 5, "Сб": 6, "Вс": 7}

DEFAULT_SCHEDULE_TIME = time(hour=8, minute=30, second=15)