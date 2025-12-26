from datetime import timedelta

from maestro.app import db
from maestro.testing import MaestroTest
from maestro.utils import local_now

from .. import queries
from ..models import SleepEvent


def test_save_and_get_last_event(mt: MaestroTest) -> None:
    # Returns default midnight asleep event when DB is empty
    last_event = queries.get_last_event()
    assert last_event.wakeup is False
    assert last_event.timestamp.hour == 0
    assert last_event.timestamp.minute == 0

    # Saving event stores to DB
    now = local_now()
    queries.save_sleep_event(timestamp=now, wakeup=True)
    events = db.session.query(SleepEvent).all()
    assert len(events) == 1

    # Getting last event returns most recent
    last_event = queries.get_last_event()
    assert last_event.wakeup is True
    assert last_event.timestamp == now


def test_delete_last_event(mt: MaestroTest) -> None:
    # Deleting when DB is empty doesn't error
    queries.delete_last_event()
    events = db.session.query(SleepEvent).all()
    assert len(events) == 0

    # Deleting removes most recent event
    now = local_now()
    queries.save_sleep_event(timestamp=now, wakeup=True)
    queries.save_sleep_event(timestamp=now + timedelta(hours=1), wakeup=False)
    events = db.session.query(SleepEvent).all()
    assert len(events) == 2

    queries.delete_last_event()
    events = db.session.query(SleepEvent).all()
    assert len(events) == 1
    assert events[0].wakeup is True


def test_get_wake_windows(mt: MaestroTest) -> None:
    start = local_now().replace(hour=8, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=12)

    # Returns empty list when no events
    windows = queries.get_wake_windows(start=start, end=end)
    assert windows == []

    # Single wake window from awake to asleep
    queries.save_sleep_event(timestamp=start + timedelta(hours=1), wakeup=True)
    queries.save_sleep_event(timestamp=start + timedelta(hours=3), wakeup=False)
    windows = queries.get_wake_windows(start=start, end=end)
    assert len(windows) == 1
    window_start, window_end = windows[0]
    assert window_start == start + timedelta(hours=1)
    assert window_end == start + timedelta(hours=3)

    # Multiple wake windows
    queries.save_sleep_event(timestamp=start + timedelta(hours=5), wakeup=True)
    queries.save_sleep_event(timestamp=start + timedelta(hours=8), wakeup=False)
    windows = queries.get_wake_windows(start=start, end=end)
    assert len(windows) == 2
    window_start, window_end = windows[1]
    assert window_start == start + timedelta(hours=5)
    assert window_end == start + timedelta(hours=8)

    # Open-ended wake window (currently awake)
    queries.save_sleep_event(timestamp=start + timedelta(hours=10), wakeup=True)
    windows = queries.get_wake_windows(start=start, end=end)
    assert len(windows) == 3
    window_start, window_end = windows[2]
    assert window_start == start + timedelta(hours=10)
    assert window_end is None

    # Asleep at start creates window with None start
    db.session.query(SleepEvent).delete()
    db.session.commit()
    queries.save_sleep_event(timestamp=start + timedelta(hours=2), wakeup=False)
    windows = queries.get_wake_windows(start=start, end=end)
    assert len(windows) == 1
    window_start, window_end = windows[0]
    assert window_start is None
    assert window_end == start + timedelta(hours=2)


def test_get_awake_time(mt: MaestroTest) -> None:
    start = local_now().replace(hour=8, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=12)

    # Returns zero when no events
    awake_time = queries.get_awake_time(start=start, end=end)
    assert awake_time == timedelta(0)

    # Calculates single wake window duration
    queries.save_sleep_event(timestamp=start + timedelta(hours=1), wakeup=True)
    queries.save_sleep_event(timestamp=start + timedelta(hours=3), wakeup=False)
    awake_time = queries.get_awake_time(start=start, end=end)
    assert awake_time == timedelta(hours=2)

    # Sums multiple wake windows
    queries.save_sleep_event(timestamp=start + timedelta(hours=5), wakeup=True)
    queries.save_sleep_event(timestamp=start + timedelta(hours=8), wakeup=False)
    awake_time = queries.get_awake_time(start=start, end=end)
    assert awake_time == timedelta(hours=5)

    # Includes open-ended wake window until end time
    queries.save_sleep_event(timestamp=start + timedelta(hours=10), wakeup=True)
    awake_time = queries.get_awake_time(start=start, end=end)
    assert awake_time == timedelta(hours=7)

    # Handles asleep at start (None start becomes start time)
    db.session.query(SleepEvent).delete()
    db.session.commit()
    queries.save_sleep_event(timestamp=start + timedelta(hours=2), wakeup=False)
    awake_time = queries.get_awake_time(start=start, end=end)
    assert awake_time == timedelta(hours=2)
