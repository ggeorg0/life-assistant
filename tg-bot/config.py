import os 
from datetime import time
from dotenv import load_dotenv

load_dotenv(override=True)

# telegram token and target user id
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TG_TARGET_ID = int(os.environ.get("TG_TARGET_ID"))

# notion token
INTEGRATION_TOKEN = os.environ.get("INTEGRATION_TOKEN")

# notion databases ids
INBOX_DATABASE_ID = os.environ.get("INBOX_DATABASE_ID")
CALENDAR_DATABASE_ID = os.environ.get("CALENDAR_DATABASE_ID")
CURRENT_TASKS_ID = os.environ.get("CURRENT_TASKS_ID")
UNI_SCHEDULE = os.environ.get("UNI_SCHEDULE")

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