from datetime import UTC, datetime, timedelta, timezone

from maestro.utils import local_now

from ..db_types import TZDateTime


def test_normalize_naive_datetime() -> None:
    # Naive datetime gets UTC timezone added
    naive_dt = datetime(2025, 12, 28, 15, 30, 0)
    result = TZDateTime._normalize_datetime(naive_dt)
    assert result is not None
    assert result.tzinfo == UTC
    assert result.year == 2025
    assert result.month == 12
    assert result.day == 28
    assert result.hour == 15
    assert result.minute == 30


def test_normalize_utc_datetime() -> None:
    # UTC datetime passes through unchanged
    utc_dt = datetime(2025, 12, 28, 15, 30, 0, tzinfo=UTC)
    result = TZDateTime._normalize_datetime(utc_dt)
    assert result == utc_dt
    assert result.tzinfo == UTC


def test_normalize_aware_datetime() -> None:
    # Timezone-aware datetime converts to UTC
    est = timezone(offset=timedelta(hours=-5))
    est_dt = datetime(2025, 12, 28, 10, 30, 0, tzinfo=est)
    result = TZDateTime._normalize_datetime(est_dt)
    assert result is not None
    assert result.tzinfo == UTC
    assert result.hour == 15

    # local_now() datetime converts to UTC
    local = local_now().replace(hour=12)
    result = TZDateTime._normalize_datetime(local)
    assert result is not None
    assert result.tzinfo == UTC
    assert result.hour == 17


def test_normalize_none() -> None:
    # None returns None
    result = TZDateTime._normalize_datetime(None)
    assert result is None
