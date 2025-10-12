from maestro.app import db


class SleepEvent(db.Model):  # type:ignore [name-defined]
    __tablename__ = "sleep_event"

    timestamp = db.Column(db.DateTime, primary_key=True, nullable=False)
    wakeup = db.Column(db.Boolean, nullable=False)

    def __repr__(self) -> str:
        return f"<SleepEvent(timestamp={self.timestamp}, wakeup={self.wakeup})>"
