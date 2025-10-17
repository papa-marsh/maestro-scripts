from datetime import timedelta

from structlog.stdlib import get_logger

from maestro.registry import person
from maestro.triggers import event_fired_trigger
from maestro.utils import Notif, local_now
from maestro.utils.dates import format_duration
from scripts.sleep_tracking.queries import (
    delete_last_event,
    get_last_event,
    get_total_sleep,
    save_sleep_event,
)

FALSE_ALARM_THRESHOLD = timedelta(minutes=15)

NOTIF_TITLE = "Sleep Tracker"
NOTIF_ID = "sleep_tracker"

log = get_logger()


def sleep_tracker_notify(message: str, emily_only: bool = False) -> None:
    target = person.emily if emily_only else [person.emily, person.marshall]
    Notif(
        message=message,
        title=NOTIF_TITLE,
        tag=NOTIF_ID,
    ).send(target)


def notif_message(duration: str, total_duration: str, wakeup: bool) -> str:
    event_text = "woke up" if wakeup else "went to sleep"
    return f"Olivia {event_text} after {duration}\nTotal sleep today: {total_duration}"


@event_fired_trigger("olivia_asleep")
def olivia_asleep() -> None:
    now = local_now()
    last_event = get_last_event()
    if not last_event.wakeup:
        sleep_tracker_notify("Olivia is already asleep")
        return

    if now - last_event.timestamp < FALSE_ALARM_THRESHOLD:
        delete_last_event()
        last_event = get_last_event()
        duration = format_duration(now - last_event.timestamp)
        sleep_tracker_notify(f"False alarm. Olivia has been asleep for {duration}")
        return

    duration = format_duration(now - last_event.timestamp)
    total_duration = format_duration(get_total_sleep())

    message = notif_message(duration, total_duration, wakeup=False)
    sleep_tracker_notify(message)
    save_sleep_event(timestamp=now, wakeup=False)


@event_fired_trigger("olivia_awake")
def olivia_awake() -> None:
    now = local_now()
    last_event = get_last_event()
    if last_event.wakeup:
        sleep_tracker_notify("Olivia is already awake")
        return

    if now - last_event.timestamp < FALSE_ALARM_THRESHOLD:
        delete_last_event()
        last_event = get_last_event()
        duration = format_duration(now - last_event.timestamp)
        sleep_tracker_notify(f"False alarm. Olivia has been awake for {duration}")
        return

    duration = format_duration(now - last_event.timestamp)
    total_duration = format_duration(get_total_sleep())

    message = notif_message(duration, total_duration, wakeup=True)
    sleep_tracker_notify(message)
    save_sleep_event(timestamp=now, wakeup=True)


@event_fired_trigger("olivia_info")
def olivia_info() -> None:
    now = local_now()
    last_event = get_last_event()

    duration = format_duration(now - last_event.timestamp)
    total_duration = format_duration(get_total_sleep())

    state = "awake" if last_event.wakeup else "asleep"
    message = f"Olivia has been {state} for {duration}\nTotal sleep today: {total_duration}"
    sleep_tracker_notify(message)
