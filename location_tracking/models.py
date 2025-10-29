from typing import ClassVar

from maestro.app import db


class ZoneChange(db.Model):  # type:ignore [name-defined]
    __tablename__ = "zone_change"
    __table_args__: ClassVar = {"extend_existing": True}

    person = db.Column(db.String, primary_key=True, nullable=False)
    arrived_at = db.Column(db.DateTime, primary_key=True, nullable=False)
    zone_name = db.Column(db.String, nullable=False)
    duration_seconds = db.Column(db.Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<ZoneChange(person={self.person}, zone_name={self.zone_name})>"
