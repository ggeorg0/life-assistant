import os

import bot

if __name__ == "__main__":
    telegram_bot = bot.run(os.environ.get("TEST_BOT_TOKEN"))

