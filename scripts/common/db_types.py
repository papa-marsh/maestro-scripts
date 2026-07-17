from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, TypeDecorator
from sqlalchemy.engine import Dialect


class TZDateTime(TypeDecorator):
    """A DateTime column that stores in UTC and converts to/from local timezone"""

    impl = DateTime
    cache_ok = True

    @staticmethod
    def _normalize_datetime(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def process_bind_param(self, value: datetime | None, _dialect: Dialect) -> Any:
        return self._normalize_datetime(value)

    def process_result_value(self, value: datetime | None, _dialect: Dialect) -> Any:
        return self._normalize_datetime(value)
