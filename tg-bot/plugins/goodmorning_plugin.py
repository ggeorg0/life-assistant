from random import choice
from datetime import datetime

from .interface import MorningMsgPlugin

PHRASES = ['Доброе утро!', 'С добрым утром!', 'Подъем!', 'Guten morgen!']

class GoodmorningPlugin(MorningMsgPlugin):
    def __init__(self) -> None:
        super().__init__()
        self._name = "goodmorning"

    def _process_message(self, message: list[str]):
        message.insert(0, choice(PHRASES))
        date_formated = datetime.now().date().strftime("%d %b %A")
        message.insert(1, f'Сегодня <b>{date_formated}</b>\n')

plg = GoodmorningPlugin
