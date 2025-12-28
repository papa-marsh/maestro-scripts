from typing import ClassVar

from maestro.app import db
from scripts.common.db_types import TZDateTime


class SleepEvent(db.Model):  # type:ignore [name-defined]
    __tablename__ = "sleep_event"
    __table_args__: ClassVar = {"extend_existing": True}

    timestamp = db.Column(TZDateTime, primary_key=True, nullable=False)
    wakeup = db.Column(db.Boolean, nullable=False)

    def __repr__(self) -> str:
        return f"<SleepEvent(timestamp={self.timestamp}, wakeup={self.wakeup})>"
