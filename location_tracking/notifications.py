from dataclasses import dataclass
from datetime import timedelta

from maestro.domains import Person
from maestro.integrations import StateChangeEvent
from maestro.registry import person
from maestro.triggers import state_change_trigger
from maestro.utils import Notif
from scripts.custom_domains import ZoneExtended


@dataclass
class ZoneChangeEvent:
    name: str
    person: Person
    spouse: Person
    notif_identifier: str
    old_zone: str
    old_zone_is_region: bool
    old_zone_prefix: str
    new_zone: str
    new_zone_is_region: bool
    new_zone_prefix: str
    debounce: timedelta


def get_zone_change_event(state_change: StateChangeEvent) -> ZoneChangeEvent:
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
        notif_identifier=f"{person_.id.entity}_zone_update",
        old_zone=state_change.old.state,
        old_zone_is_region=old_metadata.region,
        old_zone_prefix=old_metadata.prefix,
        new_zone=state_change.new.state,
        new_zone_is_region=new_metadata.region,
        new_zone_prefix=new_metadata.prefix,
        debounce=new_metadata.debounce,
    )


# @state_change_trigger(person.marshall, person.emily)
def send_location_update(state_change: StateChangeEvent) -> None:
    event = get_zone_change_event(state_change)

    if not event.new_zone_is_region:
        message = f"{event.name} arrived at {event.new_zone_prefix} {event.new_zone}"

    elif not event.old_zone_is_region:
        message = f"{event.name} left {event.old_zone_prefix} {event.old_zone}"

    elif event.new_zone != "not_home":
        message = f"{event.name} is in {event.new_zone_prefix} {event.new_zone}"

    else:
        message = f"{event.name} left {event.old_zone_prefix} {event.old_zone}"

    Notif(
        message=message,
        group=event.notif_identifier,
    ).send(event.spouse)
