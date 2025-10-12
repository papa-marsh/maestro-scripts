from datetime import datetime, timedelta

from apscheduler.job import Job
from flask import current_app
from structlog.stdlib import get_logger

from maestro.app import db
from maestro.integrations import FiredEvent
from maestro.registry import person
from maestro.triggers import event_fired_trigger
from maestro.utils import Notif, local_now

from .models import SleepEvent

log = get_logger()

# Job ID for the periodic notification job
PERIODIC_JOB_ID = "olivia_sleep_periodic_notification"


def get_last_event() -> SleepEvent | None:
    """Get the most recent sleep event."""
    return db.session.query(SleepEvent).order_by(SleepEvent.timestamp.desc()).first()


def format_duration(minutes: int) -> str:
    """Format duration in a human-readable way."""
    if minutes < 60:
        return f"{minutes} minutes"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    if remaining_minutes == 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    return f"{hours} hour{'s' if hours != 1 else ''} and {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"


def send_periodic_notification() -> None:
    """Send periodic notification about current sleep/wake status."""
    last_event = get_last_event()

    if not last_event:
        log.warning("No sleep events found for periodic notification")
        return

    now = local_now()
    duration_minutes = int((now - last_event.timestamp.replace(tzinfo=now.tzinfo)).total_seconds() / 60)

    state = "asleep" if not last_event.wakeup else "awake"
    message = f"Olivia has been {state} for {format_duration(duration_minutes)}"

    notif = Notif(message=message, title="Sleep Update")
    notif.send(person.emily)
    log.info("Sent periodic notification", state=state, duration_minutes=duration_minutes)


def schedule_periodic_notifications() -> None:
    """Schedule periodic notifications every 10 minutes."""
    scheduler = current_app.scheduler

    # Remove existing job if it exists
    existing_job: Job | None = scheduler.get_job(PERIODIC_JOB_ID)
    if existing_job:
        existing_job.remove()

    # Schedule new job starting 10 minutes from now
    scheduler.add_job(
        func=send_periodic_notification,
        trigger="interval",
        minutes=10,
        id=PERIODIC_JOB_ID,
        replace_existing=True,
        next_run_time=local_now() + timedelta(minutes=10),
    )
    log.info("Scheduled periodic notifications")


def cancel_periodic_notifications() -> None:
    """Cancel periodic notifications."""
    scheduler = current_app.scheduler
    existing_job: Job | None = scheduler.get_job(PERIODIC_JOB_ID)
    if existing_job:
        existing_job.remove()
        log.info("Cancelled periodic notifications")


@event_fired_trigger("olivia_asleep")
def handle_olivia_asleep(event: FiredEvent) -> None:
    """Handle when Olivia falls asleep."""
    now = local_now()

    # Get the last event to calculate how long she was awake
    last_event = get_last_event()

    # Create new sleep event
    sleep_event = SleepEvent(timestamp=now, wakeup=False)
    db.session.add(sleep_event)
    db.session.commit()

    log.info("Olivia fell asleep", timestamp=now)

    # Send notification
    if last_event and last_event.wakeup:
        duration_minutes = int((now - last_event.timestamp.replace(tzinfo=now.tzinfo)).total_seconds() / 60)
        message = f"Olivia went to sleep after {format_duration(duration_minutes)}"
    else:
        message = "Olivia went to sleep"

    notif = Notif(message=message, title="Sleep Event")
    notif.send(person.emily)

    # Schedule periodic notifications
    schedule_periodic_notifications()


@event_fired_trigger("olivia_awake")
def handle_olivia_awake(event: FiredEvent) -> None:
    """Handle when Olivia wakes up."""
    now = local_now()

    # Get the last event to calculate how long she was asleep
    last_event = get_last_event()

    # Create new wake event
    wake_event = SleepEvent(timestamp=now, wakeup=True)
    db.session.add(wake_event)
    db.session.commit()

    log.info("Olivia woke up", timestamp=now)

    # Send notification
    if last_event and not last_event.wakeup:
        duration_minutes = int((now - last_event.timestamp.replace(tzinfo=now.tzinfo)).total_seconds() / 60)
        message = f"Olivia woke up after {format_duration(duration_minutes)}"
    else:
        message = "Olivia woke up"

    notif = Notif(message=message, title="Sleep Event")
    notif.send(person.emily)

    # Schedule periodic notifications
    schedule_periodic_notifications()


def calculate_total_sleep_time(date: datetime | None = None) -> int:
    """
    Calculate total sleep time for a given day in minutes.

    Rules:
    - Ignores overnight sleep (sleep before first wakeup of the day)
    - Ignores intervals less than 15 minutes

    Args:
        date: The date to calculate for. Defaults to today.

    Returns:
        Total sleep time in minutes
    """
    if date is None:
        date = local_now()

    # Get start and end of day
    start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    # Get all events for the day
    events = (
        db.session.query(SleepEvent)
        .filter(SleepEvent.timestamp >= start_of_day)
        .filter(SleepEvent.timestamp < end_of_day)
        .order_by(SleepEvent.timestamp.asc())
        .all()
    )

    if not events:
        return 0

    # Find the first wakeup of the day
    first_wakeup_idx = None
    for idx, event in enumerate(events):
        if event.wakeup:
            first_wakeup_idx = idx
            break

    # If no wakeup found, return 0 (still in overnight sleep)
    if first_wakeup_idx is None:
        return 0

    # Only consider events after the first wakeup
    events_after_wakeup = events[first_wakeup_idx:]

    total_sleep_minutes = 0
    current_sleep_start = None

    for event in events_after_wakeup:
        if not event.wakeup:  # Fell asleep
            current_sleep_start = event.timestamp
        elif event.wakeup and current_sleep_start:  # Woke up
            duration_minutes = int((event.timestamp - current_sleep_start).total_seconds() / 60)
            # Only count if >= 15 minutes
            if duration_minutes >= 15:
                total_sleep_minutes += duration_minutes
            current_sleep_start = None

    # If still asleep at end of day, count up to end of day (or now if today)
    if current_sleep_start:
        end_time = min(local_now(), end_of_day)
        if end_time > current_sleep_start:
            duration_minutes = int((end_time - current_sleep_start).total_seconds() / 60)
            if duration_minutes >= 15:
                total_sleep_minutes += duration_minutes

    return total_sleep_minutes
