from random import choice, shuffle
from datetime import datetime

from .interface import ActionsCallback, MessageCallback, AbstractPlugin
from notion import Notion
from tools import protect_for_html

GOOD_MORNING_PHRASES = ['Доброе утро!', 'С добрым утром!', 'Подъем!', 'Guten morgen!']

DEFAULT_WISHES = ["Хорошего дня!", "Отличной работы", "Have a nice day!"]
HARDWORK_WISHES = ["За работу блин!", "Вперед на завод!!!", "Работаем + жоска ботаем"]
WEEKENDS_WISHES = ["Выходные! Выходные! Я забыл прооо выходные", "Хороших выходных!", "Не забывай отдыхать!"]
MONDAY_WISHES = ["С понедельничком!", "С началом рабочей недели!", "Это понедельник!", "Cнова понедельник!"]


class GoodmorningPlugin(AbstractPlugin):
    _sending_time: datetime | tuple[datetime]
    def __init__(self) -> None:
        super().__init__()
        self._name = "morningsummary"
        self._notion = Notion()
        self._sending_time = datetime(year=0, month=0, day=0, 
                                      hour=8, minute=30)

    @property
    def sending_time(self) -> datetime | tuple[datetime]:
        return self._sending_time
    
    @sending_time.setter
    def sending_time(self, value: datetime | tuple[datetime]):
        self._sending_time = value

    def _fmt_event_time(self, event):
        result = ''
        if event['end']:
            result = event['start'].strftime(" %d/%m")
        if event['start'].hour or event['start'].minute:
            result = result + event['start'].strftime(" %H:%M")
        if event['end']:
            result = result + event['end'].strftime(" — %d/%m")
            if event['end'].hour or event['end'].minute:
                result = result + event['end'].strftime(" %H:%M")
        return result

    def _gather_base_summary(self, calendar, current_tasks):
        lines = []
        events = [] 
        now = datetime.now()
        for event in calendar:
            if now.date() == event['start'].date() or (now.date() >= event['start'].date()
                                                       and event['end']
                                                       and event['end'].date() >= now.date()):
                line = ' > ' + event['title'] + self._fmt_event_time(event)
                events.append(protect_for_html(line))
        if events:
            lines.append("<b>События календаря:</b>")
            events[-1] = events[-1] + '\n'
            lines += events
        lines.append('<b>5 случайных текущих задач:</b>')
        shuffle(current_tasks)
        for task in current_tasks[:5]:
            lines.append(protect_for_html(' > ' + task))
        lines[-1] = lines[-1] + '\n'
        return lines
    
    def _say_goodmorning(self, message: list[str]):
        message.insert(0, choice(GOOD_MORNING_PHRASES))
        date_formated = datetime.now().date().strftime("%d %b %A")
        message.insert(1, f'Сегодня <b>{date_formated}</b>\n')

    def _wish_goodday(self, message: list[str]):
        pool = DEFAULT_WISHES
        if len(message) > 16:
            pool = pool + HARDWORK_WISHES
        weekday = datetime.now().weekday()
        if 5 <= weekday < 7:
            pool = pool + WEEKENDS_WISHES
        elif weekday == 0:
            pool = pool + MONDAY_WISHES
        message.append(choice(pool))

    async def morning_message(self) -> str:
        calendar = await self._notion.today_calendar_events()
        tasks = await self._notion.current_tasks()
        message_data = self._gather_base_summary(calendar, tasks)
        self._say_goodmorning(message_data)
        self._wish_goodday(message_data)
        return "\n".join(message_data)

    def message_callabacks(self) -> tuple[MessageCallback, ...]:
        if isinstance(self.sending_time, datetime):
            return ((self.sending_time, self.morning_message, 'daily'), )
        return tuple( (st, self.morning_message, 'daily') 
                     for st in self.sending_time)
    
    def actions_callbacks(self) -> tuple[ActionsCallback, ...]:
        return ()

plg = GoodmorningPlugin
