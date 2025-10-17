from datetime import datetime, timedelta

from maestro.app import db
from maestro.utils.dates import local_now
from scripts.sleep_tracking.models import SleepEvent


def save_sleep_event(timestamp: datetime, wakeup: bool) -> None:
    wake_event = SleepEvent(timestamp, wakeup)
    db.session.add(wake_event)
    db.session.commit()


def get_last_event() -> SleepEvent:
    """Get the most recent sleep event."""
    latest_event = db.session.query(SleepEvent).order_by(SleepEvent.timestamp.desc()).first()
    if not isinstance(latest_event, SleepEvent):
        raise TypeError

    return latest_event


def get_total_sleep(date: datetime | None = None) -> timedelta:
    """
    Calculate total sleep time for a given day.
    Ignores intervals less than FALSE_ALARM_THRESHOLD.
    """
    from scripts.sleep_tracking.main import FALSE_ALARM_THRESHOLD

    date = local_now() if date is None else date

    start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    events: list[SleepEvent] = (
        db.session.query(SleepEvent)
        .filter(SleepEvent.timestamp >= start_of_day)
        .filter(SleepEvent.timestamp < end_of_day)
        .order_by(SleepEvent.timestamp.asc())
        .all()
    )

    if not events:
        return timedelta()

    total_sleep = timedelta()
    current_sleep_start: datetime | None = start_of_day

    for event in events:
        if not isinstance(event.wakeup, bool) or not isinstance(event.timestamp, datetime):
            raise TypeError

        if not event.wakeup:
            current_sleep_start = event.timestamp
        elif event.wakeup and current_sleep_start:
            duration = event.timestamp - current_sleep_start
            if duration.total_seconds() >= FALSE_ALARM_THRESHOLD:
                total_sleep += event.timestamp - current_sleep_start
            current_sleep_start = None

    if current_sleep_start:
        end_time = min(local_now(), end_of_day)
        if end_time > current_sleep_start:
            total_sleep += end_time - current_sleep_start

    return total_sleep
