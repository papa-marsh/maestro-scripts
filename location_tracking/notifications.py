from dataclasses import dataclass
from datetime import datetime, timedelta

from maestro.domains import Person
from maestro.integrations import StateChangeEvent
from maestro.registry import person
from maestro.triggers import state_change_trigger
from maestro.utils import JobScheduler, Notif, format_duration, local_now
from scripts.custom_domains import ZoneExtended
from scripts.location_tracking.queries import (
    get_last_left_home,
    get_last_zone_arrival,
    set_last_left_home,
    set_last_zone_arrival,
)

NOTIF_IDENTIFIER = "zone_update"
JOB_ID_PREFIX = "zone_update_job_"


@dataclass
class ZoneChangeEvent:
    name: str
    person: Person
    spouse: Person
    timestamp: datetime
    old_zone: str
    old_zone_is_region: bool
    old_zone_full: str
    new_zone: str
    new_zone_is_region: bool
    new_zone_full: str
    debounce: timedelta


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
        old_zone_full=f"{old_metadata.prefix} {state_change.old.state}".lstrip(),
        new_zone=state_change.new.state,
        new_zone_is_region=new_metadata.region,
        new_zone_full=f"{new_metadata.prefix} {state_change.new.state}".lstrip(),
        debounce=new_metadata.debounce,
    )


@state_change_trigger(person.marshall, person.emily)
def location_update_orchestrator(state_change: StateChangeEvent) -> None:
    event = build_zone_change_event(state_change)
    scheduler = JobScheduler(redis_client=event.person.state_manager.redis_client)
    job_id = JOB_ID_PREFIX + event.person.id.entity

    scheduler.cancel_job(job_id)

    if event.debounce == timedelta():
        send_location_update(event)
        return

    scheduler.schedule_job(
        run_time=local_now() + event.debounce,
        func=send_location_update,
        func_params={"event": event},
        job_id=job_id,
    )


def send_location_update(event: ZoneChangeEvent) -> None:
    if not event.new_zone_is_region:
        message = f"{event.name} arrived at {event.new_zone_full}"

        if event.new_zone == "home" and (left_home := get_last_left_home(event)):
            duration = format_duration(event.timestamp - left_home)
            message += f" after {duration}"
            Notif(
                title="New Zone Tracking",  # TODO: Remvoe
                message=f"You were away for {duration}",
                group=NOTIF_IDENTIFIER,
                # ).send(event.person)
            ).send(person.marshall)

    elif not event.old_zone_is_region:
        message = f"{event.name} left {event.old_zone_full}"

        if event.old_zone == "home":
            set_last_left_home(event)

        elif prev_zone_arrival_time := get_last_zone_arrival(event):
            time_at_zone = format_duration(event.timestamp - prev_zone_arrival_time)
            Notif(
                title="New Zone Tracking",  # TODO: Remvoe
                message=f"You spent {time_at_zone} at {event.old_zone_full}",
                group=NOTIF_IDENTIFIER,
                # ).send(event.person)
            ).send(person.marshall)

    elif event.new_zone != "not_home":
        message = f"{event.name} is in {event.new_zone_full}"

    else:
        message = f"{event.name} left {event.old_zone_full}"

    set_last_zone_arrival(event)

    Notif(
        title="New Zone Tracking",  # TODO: Remvoe
        message=message,
        group=NOTIF_IDENTIFIER,
        # ).send(event.spouse)
    ).send(person.marshall)
