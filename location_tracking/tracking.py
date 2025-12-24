from datetime import UTC, datetime

from maestro.app import db
from maestro.config import TIMEZONE
from maestro.integrations import StateChangeEvent
from maestro.registry import person
from maestro.triggers import state_change_trigger

from .models import ZoneChange


@state_change_trigger(person.marshall, person.emily)
def save_zone_change(state_change: StateChangeEvent) -> None:
    entity_id = state_change.entity_id
    zone_name = state_change.new.state
    arrival_time = state_change.time_fired

    previous_zone_change: ZoneChange | None = (
        db.session.query(ZoneChange)
        .filter(ZoneChange.person == entity_id)
        .order_by(ZoneChange.arrived_at.desc())
        .first()
    )

    if previous_zone_change is not None:
        update_zone_duration(
            previous_zone_change=previous_zone_change,
            departure_time=arrival_time,
        )

    new_zone_change = ZoneChange(
        person=entity_id,
        arrived_at=arrival_time,
        zone_name=zone_name,
        duration_seconds=None,
    )

    db.session.add(new_zone_change)
    db.session.commit()


def update_zone_duration(previous_zone_change: ZoneChange, departure_time: datetime) -> None:
    """Update the duration of the previous zone change based on the new arrival time."""
    prev_arrival = previous_zone_change.arrived_at

    if not isinstance(prev_arrival, datetime):
        raise TypeError

    if prev_arrival.tzinfo is None:
        prev_arrival = prev_arrival.replace(tzinfo=UTC).astimezone(TIMEZONE)

    duration = (departure_time - prev_arrival).total_seconds()
    previous_zone_change.duration_seconds = int(duration)
