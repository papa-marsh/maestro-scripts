from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from maestro.app import db
from maestro.config import TIMEZONE
from maestro.domains import Person
from maestro.integrations import StateChangeEvent
from maestro.registry import person
from maestro.triggers import state_change_trigger
from maestro.utils import IntervalSeconds, Notif, format_duration
from scripts.custom_domains import ZoneExtended
from scripts.location_tracking.models import ZoneChange

LAST_LEFT_HOME_KEY_PREFIX = "LAST_LEFT_HOME"
NOTIF_IDENTIFIER = "zone_update"


@dataclass
class ZoneChangeEvent:
    name: str
    person: Person
    spouse: Person
    timestamp: datetime
    old_zone: str
    old_zone_is_region: bool
    old_zone_prefix: str
    new_zone: str
    new_zone_is_region: bool
    new_zone_prefix: str
    debounce: timedelta


# @state_change_trigger(person.marshall, person.emily)
def send_location_update(state_change: StateChangeEvent) -> None:
    event = build_zone_change_event(state_change)

    if not event.new_zone_is_region:
        message = f"{event.name} arrived at {event.new_zone_prefix} {event.new_zone}"

        if event.new_zone == "home" and (left_home := get_last_left_home(event)):
            duration = format_duration(event.timestamp - left_home)
            message += f" after {duration}"
            Notif(
                message=f"You were away for {duration}",
                group=NOTIF_IDENTIFIER,
            ).send(event.person)

    elif not event.old_zone_is_region:
        message = f"{event.name} left {event.old_zone_prefix} {event.old_zone}"

        if event.old_zone == "home":
            set_last_left_home(event)

        prev_zone_arrival_time = get_last_zone_arrival(event.old_zone)
        if event.old_zone != "home" and prev_zone_arrival_time:
            time_at_zone = format_duration(event.timestamp - prev_zone_arrival_time)
            Notif(
                message=f"You spent {time_at_zone} at {event.old_zone_prefix} {event.old_zone}",
                group=NOTIF_IDENTIFIER,
            ).send(event.person)

    elif event.new_zone != "not_home":
        message = f"{event.name} is in {event.new_zone_prefix} {event.new_zone}"

    else:
        message = f"{event.name} left {event.old_zone_prefix} {event.old_zone}"

    Notif(
        message=message,
        group=NOTIF_IDENTIFIER,
    ).send(event.spouse)


def build_zone_change_event(state_change: StateChangeEvent) -> ZoneChangeEvent:
    person_ = state_change.entity_id.resolve_entity()
    spouse = person.emily if person_ == person.marshall else person.marshall
    if not isinstance(person_, Person):
        raise TypeError

    old_metadata = ZoneExtended.get_zone_metadata(state_change.old.state)
    new_metadata = ZoneExtended.get_zone_metadata(state_change.new.state)

    return ZoneChangeEvent(
        name=person_.friendly_name,
        person=person_,
        spouse=spouse,
        timestamp=state_change.time_fired,
        old_zone=state_change.old.state,
        old_zone_is_region=old_metadata.region,
        old_zone_prefix=old_metadata.prefix,
        new_zone=state_change.new.state,
        new_zone_is_region=new_metadata.region,
        new_zone_prefix=new_metadata.prefix,
        debounce=new_metadata.debounce,
    )


def get_last_left_home(event: ZoneChangeEvent) -> datetime | None:
    redis = event.person.state_manager.redis_client
    last_left_home_key = redis.build_key(LAST_LEFT_HOME_KEY_PREFIX, event.person.id)

    timestamp_string = redis.get(key=last_left_home_key)

    return datetime.fromisoformat(timestamp_string) if timestamp_string else None


def set_last_left_home(event: ZoneChangeEvent) -> None:
    redis = event.person.state_manager.redis_client
    last_left_home_key = redis.build_key(LAST_LEFT_HOME_KEY_PREFIX, event.person.id)

    redis.set(
        key=last_left_home_key,
        value=event.timestamp.isoformat(),
        ttl_seconds=IntervalSeconds.THIRTY_DAYS,
    )


def get_last_zone_arrival(zone_name: str) -> datetime | None:
    zone_change: ZoneChange | None = (
        db.session.query(ZoneChange)
        .filter(ZoneChange.zone_name == zone_name)
        .order_by(ZoneChange.arrived_at.desc())
        .first()
    )
    if zone_change is None:
        return None

    arrived_at = zone_change.arrived_at
    if not isinstance(arrived_at, datetime):
        raise TypeError

    if arrived_at.tzinfo is None:
        arrived_at = arrived_at.replace(tzinfo=UTC).astimezone(TIMEZONE)

    return arrived_at
