from maestro.registry import person
from maestro.triggers import event_fired_trigger
from maestro.utils import Notif, local_now
from maestro.utils.dates import IntervalSeconds, format_duration
from scripts.sleep_tracking.queries import get_last_event, get_total_sleep, save_sleep_event

FALSE_ALARM_THRESHOLD = IntervalSeconds.FIFTEEN_MINUTES

NOTIF_TITLE = "Sleep Tracker"
NOTIF_ID = "sleep_tracker"


def sleep_tracker_notify(message: str, emily_only: bool = True) -> None:
    target = person.emily if emily_only else [person.emily, person.marshall]
    Notif(
        message=message,
        title=NOTIF_TITLE,
        tag=NOTIF_ID,
        group=NOTIF_ID,
    ).send(target)


@event_fired_trigger("olivia_asleep")
def olivia_asleep() -> None:
    now = local_now()
    last_event = get_last_event()
    if not last_event.wakeup:
        sleep_tracker_notify("Olivia is already asleep")
        return

    duration = format_duration(now - last_event.timestamp)
    total_duration = format_duration(get_total_sleep())

    if now - last_event.timestamp < FALSE_ALARM_THRESHOLD:
        sleep_tracker_notify(f"False alarm. Olivia has been asleep for {duration}")
        return

    message = f"Olivia went to sleep after {duration} (Total today: {total_duration})"

    sleep_tracker_notify(message, emily_only=False)
    save_sleep_event(timestamp=now, wakeup=False)


@event_fired_trigger("olivia_awake")
def olivia_awake() -> None:
    now = local_now()
    last_event = get_last_event()
    if last_event.wakeup:
        sleep_tracker_notify("Olivia is already awake")
        return

    duration = format_duration(now - last_event.timestamp)
    total_duration = format_duration(get_total_sleep())

    if now - last_event.timestamp < FALSE_ALARM_THRESHOLD:
        sleep_tracker_notify(f"False alarm. Olivia has been awake for {duration}")
        return
    message = f"Olivia woke up after {duration} (Total today: {total_duration})"

    sleep_tracker_notify(message, emily_only=False)
    save_sleep_event(timestamp=now, wakeup=True)


@event_fired_trigger("olivia_info")
def olivia_info() -> None:
    now = local_now()
    last_event = get_last_event()

    duration = format_duration(now - last_event.timestamp)
    total_duration = format_duration(get_total_sleep())

    state = "awake" if last_event.wakeup else "asleep"
    sleep_tracker_notify(f"Olivia has been {state} for {duration} (Total today: {total_duration})")
