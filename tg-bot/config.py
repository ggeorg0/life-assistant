import os 
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

# other hyperparameters
DEPTH_LIMIT = 16
PAGE_SIZE = 25

