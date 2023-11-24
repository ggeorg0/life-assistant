from datetime import datetime, date, time, timedelta
from typing import Callable, Sequence, Any
import textwrap

from plugins.interface import AbstractPlugin, ActionsCallbackTuple, MessageCallbackTuple
from notion import Notion
from tools import protect_for_html, time_from_args
from config import DEFAULT_SCHEDULE_TIME



class UniSchedule(AbstractPlugin):
    _send_time: time

    def __init__(self, sending_time: time=DEFAULT_SCHEDULE_TIME) -> None:
        super().__init__("UniSchedule")
        self._notion = Notion()
        self._send_time = sending_time

    @property
    def message_callabacks(self) -> tuple[MessageCallbackTuple, ...]:
        send_datetime = datetime.combine(date.today(), self._send_time)
        return ((send_datetime, self.today, 'daily'), )
    
    @property
    def actions_callbacks(self) -> tuple[ActionsCallbackTuple, ...]:
        # return ( (datetime.combine(datetime.today(), self._send_time.time()), 
        #           self.some_action, 'daily'), )
        return ()
    
    async def form_schedule_message(self, day: date) -> str:
        daily_schedule = await self._notion.uni_daily_schedule(day)
        daily_schedule = sorted(daily_schedule)
        message = ["Расписание на сегодня:",
                   "<pre>%-2s %-5s %-7s %-20s" % ("#", "нач.", "каб.", "предмет"),
                   "-"*38]
        timeline_flag = True
        for num, pair_time, subj, _, auditory in daily_schedule:
            ptime = time(*pair_time[1])
            message_line = "%-2s %-2s:%-2s %-7s %-20s" % (num,
                                                          ptime.hour, ptime.minute,
                                                          auditory, 
                                                          subj)
            message_line = protect_for_html(message_line)
            message_line = textwrap.wrap(message_line, width=38, 
                                         subsequent_indent=' '*17)
            # current timeline
            if (datetime.now() < datetime.combine(date.today(), ptime)
                    and timeline_flag):
                message_line.insert(0, protect_for_html('>' + '- '*18 + '<'))
                timeline_flag = False

            message.append('\n'.join(message_line ) + '\n')
        message[-1] = message[-1] + "</pre>"
        return '\n'.join(message)
        
    async def today(self, *args) -> str:
        return await self.form_schedule_message(date.today())
    
    async def tomorrow(self, *args) -> str:
        return await self.form_schedule_message(date.today()
                                                + timedelta(days=1))
    async def yesterday(self, *args) -> str:
        return await self.form_schedule_message(date.today()
                                                - timedelta(days=1))
    
    async def set_sending_time(self, *args):
        time_or_exc = time_from_args(args)
        if type(time_or_exc) != time:
            return time_or_exc
        self._send_time = time_or_exc
        return "New schedule send time:" + time_or_exc.strftime("%H:%M:%S")

    
plg = UniSchedule