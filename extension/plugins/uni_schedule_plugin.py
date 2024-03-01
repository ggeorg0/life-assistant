from datetime import datetime, date, time, timedelta
import textwrap

from extension import AbstractPlugin, ActionResult
from extension.exttypes import CommandBindingsT, EventsScheduleT
from notion import Notion
from tools import protect_for_html, time_from_args, dt_from_time
from config import (
    TODAY_SCHED_TIME,
    TOMMOROW_SCHED_TIME,
    TIMEZONE,
)

class UniSchedule(AbstractPlugin):
    __slots__ = (
        "_td_send_time",
        "_notion",
        "_tm_send_enabled",
        "_tm_send_time"
    )
    _notion: Notion
    _td_send_time: time
    _tm_send_enabled: bool
    _tm_send_time: time

    # Note: Plugin methods should return `datetime` (not `time`),
    #   but, for daily events date part is ignored, so
    #   there is a temorary date wich will be combined with time

    def __init__(self,
                 td_schedule_send: time=TODAY_SCHED_TIME,
                 tom_schedule_send: time=TOMMOROW_SCHED_TIME):
        super().__init__("UniSchedule")
        self._notion = Notion()
        self._td_send_time = td_schedule_send
        self._tm_send_enabled = True
        self._tm_send_time = tom_schedule_send

    def user_commands(self) -> CommandBindingsT:
        return (
            ("schedule", self.today),
            ("yschedule", self.yesterday),
            ("tschedule", self.tomorrow),
            ("schedule_settime", self.set_sending_time),
            ("tschedule_settime", self.set_tm_sending_time),
            ("tschedule_togglesend", self.toggle_send_tomorrow),
        )

    def help(self, *args) -> dict[str, tuple[str, ...]]:
        return {
            "Today's schedule":
                ('/schedule', ),
            "Yesterday's schedule":
                ('/yschedule', ),
            "Tommorow's schedule":
                ('/tschedule', ),
            "Set schedule send today's, tommorow's,time ":
                ('/schedule_settime <time>', '/tschedule_settime <time>'),
            "Toggle tommorow's schedule send":
                ('/tschedule_togglesend', ),
        }

    def daily_events(self) -> EventsScheduleT:
        td_datetime = dt_from_time(self._td_send_time)
        tmr_datetime = dt_from_time(self._tm_send_time)
        return (
            (td_datetime, self.today),
            (tmr_datetime, self.tomorrow_autosend)
        )

    def monthly_events(self) -> EventsScheduleT:
        return ()

    def disordered_events(self) -> EventsScheduleT:
        return ()

    async def form_schedule_message(self, day: date) -> str:
        daily_schedule = await self._notion.uni_daily_schedule(day)
        daily_schedule = sorted(daily_schedule)
        message = ["%-2s %-5s %-7s %-20s" % ("#", "нач.", "каб.", "предмет"),
                   "-"*38]
        timeline_flag = True
        for num, pair_time, subj, _, auditory in daily_schedule:
            ptime = time(*pair_time[1], tzinfo=TIMEZONE)
            message_line = "%-2s %-2s:%-2s %-7s %-20s" % (
                num,
                ptime.hour, ptime.minute,
                auditory,
                subj
            )
            message_line = protect_for_html(message_line)
            message_line = textwrap.wrap(message_line, width=38,
                                         subsequent_indent=' '*17)
            # current timeline
            if (datetime.now(TIMEZONE) < dt_from_time(ptime) and timeline_flag):
                message_line.insert(0, protect_for_html('>' + '- '*18 + '<'))
                timeline_flag = False
            message.append('\n'.join(message_line ) + '\n')
        return "<pre>" + '\n'.join(message) + "</pre>"

    async def today(self, *args) -> ActionResult:
        message=await self.form_schedule_message(date.today())
        return ActionResult("Расписание на сегодня:\n" + message)

    async def tomorrow(self, *args) -> ActionResult:
        message = await self.form_schedule_message(date.today()
                                                   + timedelta(days=1))
        return ActionResult("Расписание на завтра:\n" + message)

    async def yesterday(self, *args) -> ActionResult:
        message=await self.form_schedule_message(date.today()
                                                 - timedelta(days=1))
        return ActionResult("Вчерашнее расписание:\n" + message)

    async def tomorrow_autosend(self, *args) -> ActionResult:
        if self._tm_send_enabled:
            return await self.tomorrow(self, *args)
        return ActionResult()

    async def set_sending_time(self, *args) -> ActionResult:
        time_or_exc = time_from_args(args)
        if isinstance(time_or_exc, str):
            return ActionResult(message=time_or_exc)
        self._td_send_time = time_or_exc
        return ActionResult(
            message=("New schedule send time:" +
                     time_or_exc.strftime("%H:%M:%S") + "\n" +
                     "Please, reload daily events to apply this change")
        )

    async def toggle_send_tomorrow(self, *args: str) -> ActionResult:
        if 0 < len(args) < 2:
            match args[0].upper():
                case "ON":
                    self._tm_send_enabled = True
                    return ActionResult(
                        "enabled auto sending schedule for tommorow"
                    )
                case "OFF":
                    self._tm_send_enabled = False
                    return ActionResult(
                        "diabled auto sending schedule for tommorow"
                    )
        return ActionResult("invalid arguments, use `on` or `off`")

    async def set_tm_sending_time(self, *args) -> ActionResult:
        time_or_exc = time_from_args(args)
        if isinstance(time_or_exc, str):
            return ActionResult(message=time_or_exc)
        self._tm_send_time = time_or_exc
        return ActionResult(
            message=("New send time of schedule for tommorow :" +
                     time_or_exc.strftime("%H:%M:%S") + "\n" +
                     "Please, reload daily events to apply this change")
        )
