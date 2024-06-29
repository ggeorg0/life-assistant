from random import choice, shuffle
from datetime import datetime

from extension import AbstractPlugin, ActionResult
from extension.exttypes import CommandBindingsT, EventsScheduleT
from mynotion import Notion
from tools import protect_for_html, dt_from_time, time_from_args
from config import MORNING_MESSAGE_TIME

GOOD_MORNING_PHRASES = [
    'Доброе утро!',
    'С добрым утром!',
    'Подъем!',
    'Guten morgen!'
]
DEFAULT_WISHES = [
    "Хорошего дня!",
    "Отличной работы",
    "Have a nice day!"
]
HARDWORK_WISHES = [
    "За работу блин!",
    "Вперед на завод!!!",
    "Работаем + жоска ботаем"
]
WEEKENDS_WISHES = [
    "Выходные! Выходные! Я забыл прооо выходные",
    "Хороших выходных!",
    "Не забывай отдыхать!"
]
MONDAY_WISHES = [
    "С понедельничком!",
    "С началом рабочей недели!",
    "Это понедельник!",
    "Cнова понедельник!"
]


class MorningSummary(AbstractPlugin):
    _send_dtime: datetime
    def __init__(self) -> None:
        super().__init__("MorningSummary")
        self._notion = Notion()
        self._send_dtime = dt_from_time(MORNING_MESSAGE_TIME)

    def user_commands(self) -> CommandBindingsT:
        return (
            ("morning", self.morning_message),
            ("morning_sendtime", self.clarify_send_time)
        )

    def help(self, *args) -> dict[str, tuple[str, ...]]:
        return {
            "Show \"morning message\" now":
                ('/morning', ),
            "Update \"morning message\" sending time. "
            "Send it without arguments to find out the current value":
                ('/morning_sendtime [time]', ),
        }

    def daily_events(self) -> EventsScheduleT:
        return (
            (self._send_dtime, self.morning_message),
        )

    def monthly_events(self) -> EventsScheduleT:
        return ()

    def disordered_events(self) -> EventsScheduleT:
        return ()

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

    async def morning_message(self, *args) -> ActionResult:
        calendar = await self._notion.get_calendar_events()
        tasks = await self._notion.get_current_tasks()
        tasks = list(tasks.values())
        message_data = self._gather_base_summary(calendar, tasks)
        self._say_goodmorning(message_data)
        self._wish_goodday(message_data)
        return ActionResult("\n".join(message_data))

    async def clarify_send_time(self, *args) -> ActionResult:
        if len(args) < 1:
            return ActionResult(str(self._send_dtime.time()))
        else:
            return self.set_send_time(*args)

    def set_send_time(self, *args) -> ActionResult:
        new_time = time_from_args(args)
        if isinstance(new_time, str):
            return ActionResult(new_time)
        self._send_dtime = dt_from_time(new_time)
        return ActionResult("New morning message time: "
                            f"{self._send_dtime.time()}")
