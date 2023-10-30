from random import choice
from datetime import datetime

from .interface import MorningMsgPlugin

DEFAULT_WISHES = ["Хорошего дня!", "Отличной работы", "Have a nice day!"]
HARDWORK_WISHES = ["За работу блин!", "Вперед на завод!!!", "Работаем + жоска ботаем"]
WEEKENDS = ["Выходные! Выходные! Я забыл прооо выходные", "Хороших выходных!", "Не забывай отдыхать!"]
MONDAY = ["С понедельничком!", "С началом рабочей недели!", "Это понедельник!", "Cнова понедельник!"]


class HaveanicedayPlugin(MorningMsgPlugin):
    def __init__(self) -> None:
        super().__init__()
        self._name = "haveaniceday"

    def _process_message(self, message: list[str]):
        pool = DEFAULT_WISHES
        if len(message) > 16:
            pool = pool + HARDWORK_WISHES
        weekday = datetime.now().weekday()
        if 5 <= weekday < 7:
            pool = pool + WEEKENDS
        elif weekday == 0:
            pool = pool + MONDAY
        message.append(choice(pool))

plg = HaveanicedayPlugin