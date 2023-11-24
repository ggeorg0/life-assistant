from datetime import time
from typing import Sequence

TIMESET_HELP_MSG = "You should provide your command \
with hours minutes ands seconds in this fashon:\n \
/your_command HH MM SS \
"

def protect_for_html(text_data):
    return text_data.replace('&', '&amp;')\
                    .replace('<', '&lt;')\
                    .replace('>', '&gt;')

def singleton(cls, *args, **kw):
    instances = {}
    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton

def time_from_args(args: Sequence) -> time | str:
    try:
        hours = int(args[0])
        minutes = int(args[1])
        seconds = int(args[2])
        return time(hours, minutes, seconds)
    except IndexError:
        return TIMESET_HELP_MSG
    except ValueError as ve:
        if "invalid literal for int()" in ve.args[0]:
            return TIMESET_HELP_MSG
        return str(ve.args[0])
    # except Exception as exc:
        # return f"Some exception occured during time extraction: {exc}"

