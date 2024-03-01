from datetime import time, datetime, timedelta

from extension import AbstractPlugin, ActionResult
from extension.exttypes import CommandBindingsT, EventsScheduleT
from tools import time_from_args, dt_from_time
from config import TIMEZONE

class TimerPlugin(AbstractPlugin):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(name="Timer")

    def user_commands(self) -> CommandBindingsT:
        return (
            ("timerset", self.set_timer),
            ("settimer", self.set_timer),
        )

    def help(self, *args) -> dict[str, tuple[str, ...]]:
        return {
            "Set timer. Send HH:MM:SS: or HH:MM as argument":
                ('/timerset <time>', '/settimer <time>'),
        }

    async def set_timer(self, *args) -> ActionResult:
        ttime = time_from_args(args)
        if isinstance(ttime, str):
            return ActionResult(ttime)  # return error message
        tdelta = timedelta(
            hours=ttime.hour,
            minutes=ttime.minute,
            seconds=ttime.second
            )
        beep = self.timer_beep_factory(tdelta)
        return ActionResult(
            message="Timer is set",
            next_datetime=datetime.now(TIMEZONE) + tdelta,
            next_action=beep
        )

    def timer_beep_factory(self, timertime: timedelta):
        async def timer_beep(*args) -> ActionResult:
            return ActionResult(f"Ring!!! {timertime} is done")
        return timer_beep

    def daily_events(self) -> EventsScheduleT:
        return ()

    def monthly_events(self) -> EventsScheduleT:
        return ()

    def disordered_events(self) -> EventsScheduleT:
        return ()
