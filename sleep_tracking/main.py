from datetime import timedelta

from structlog.stdlib import get_logger

from maestro.domains import Person
from maestro.integrations import FiredEvent
from maestro.registry import person
from maestro.triggers import event_fired_trigger
from maestro.utils import Notif, format_duration, local_now
from scripts.utils.secrets import USER_ID_TO_PERSON

from .queries import (
    delete_last_event,
    get_last_event,
    get_sleep_history,
    get_total_sleep,
    save_sleep_event,
)

FALSE_ALARM_THRESHOLD = timedelta(minutes=15)

NOTIF_TITLE = "Sleep Tracker"
NOTIF_ID = "sleep_tracker"

log = get_logger()


def sleep_tracker_notify(
    message: str,
    target: Person | list[Person] = [person.marshall, person.emily],
) -> None:
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
    save_sleep_event(timestamp=now, wakeup=False)
    total_duration = format_duration(get_total_sleep())

    message = notif_message(duration, total_duration, wakeup=False)
    sleep_tracker_notify(message)


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
    save_sleep_event(timestamp=now, wakeup=True)
    total_duration = format_duration(get_total_sleep())

    message = notif_message(duration, total_duration, wakeup=True)
    sleep_tracker_notify(message)


@event_fired_trigger("olivia_info")
def olivia_info(event: FiredEvent) -> None:
    now = local_now()
    last_event = get_last_event()

    duration = format_duration(now - last_event.timestamp)
    total_duration = format_duration(get_total_sleep())

    state = "awake" if last_event.wakeup else "asleep"
    message = (
        f"Olivia has been {state} for {duration}\n"
        "Long press for more\n\n"
        f"Total sleep today: {total_duration}"
    )

    for sleep_period in get_sleep_history():
        start, end = sleep_period
        start_str = start.strftime("%-I:%M%P")
        end_str = end.strftime("%-I:%M%P")
        duration = format_duration(end - start)
        message += f"\n{start_str}-{end_str} ({duration})"

    if target := USER_ID_TO_PERSON.get(event.user_id or ""):
        sleep_tracker_notify(message, target)
