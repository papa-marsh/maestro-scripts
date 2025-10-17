from datetime import UTC, datetime, timedelta

from maestro.app import db
from maestro.config import TIMEZONE
from maestro.utils.dates import local_now
from scripts.sleep_tracking.models import SleepEvent


def save_sleep_event(timestamp: datetime, wakeup: bool) -> None:
    sleep_event = SleepEvent(timestamp=timestamp, wakeup=wakeup)
    db.session.add(sleep_event)
    db.session.commit()


def get_last_event() -> SleepEvent:
    """Get the most recent sleep event."""
    latest_event = db.session.query(SleepEvent).order_by(SleepEvent.timestamp.desc()).first()

    if latest_event is None:
        this_morning_at_midnight = local_now().replace(hour=0, minute=0, second=0, microsecond=0)
        latest_event = SleepEvent(timestamp=this_morning_at_midnight, wakeup=False)

    if not isinstance(latest_event, SleepEvent):
        raise TypeError

    if latest_event.timestamp.tzinfo is None:
        latest_event.timestamp = latest_event.timestamp.replace(tzinfo=UTC).astimezone(TIMEZONE)

    return latest_event


def delete_last_event() -> None:
    """Delete the most recent sleep event."""
    latest_event = db.session.query(SleepEvent).order_by(SleepEvent.timestamp.desc()).first()
    if latest_event:
        db.session.delete(latest_event)
        db.session.commit()


def get_sleep_history(
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[tuple[datetime, datetime]]:
    """Return a list of sleep period tuples: (start, end) for the given time interval"""
    if start is None:
        start = local_now().replace(hour=0, minute=0, second=0, microsecond=0)
    if end is None:
        end = local_now()

    events: list[SleepEvent] = (
        db.session.query(SleepEvent)
        .filter(SleepEvent.timestamp >= start)
        .filter(SleepEvent.timestamp < end)
        .order_by(SleepEvent.timestamp.asc())
        .all()
    )

    if not events:
        return []

    sleep_periods: list[tuple[datetime, datetime]] = []
    current_sleep_start: datetime | None = None

    for event in events:
        if not isinstance(event.wakeup, bool) or not isinstance(event.timestamp, datetime):
            raise TypeError

        if event.timestamp.tzinfo is None:
            event.timestamp = event.timestamp.replace(tzinfo=UTC).astimezone(TIMEZONE)

        if not event.wakeup:
            current_sleep_start = event.timestamp
        elif event.wakeup and current_sleep_start:
            sleep_periods.append((current_sleep_start, event.timestamp))
            current_sleep_start = None

    if current_sleep_start:
        sleep_periods.append((current_sleep_start, min(local_now(), end)))

    return sleep_periods


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

        if event.timestamp.tzinfo is None:
            event.timestamp = event.timestamp.replace(tzinfo=UTC).astimezone(TIMEZONE)

        if not event.wakeup:
            current_sleep_start = event.timestamp
        elif event.wakeup and current_sleep_start:
            duration = event.timestamp - current_sleep_start
            if duration >= FALSE_ALARM_THRESHOLD:
                total_sleep += event.timestamp - current_sleep_start
            current_sleep_start = None

    if current_sleep_start:
        end_time = min(local_now(), end_of_day)
        if end_time > current_sleep_start:
            total_sleep += end_time - current_sleep_start

    return total_sleep
