from datetime import timedelta

from maestro.domains import ON, Person
from maestro.integrations import StateChangeEvent
from maestro.registry import person
from maestro.triggers import state_change_trigger
from maestro.utils import Notif, local_now

from .door_left_open import EXTERIOR_DOORS


@state_change_trigger(*EXTERIOR_DOORS, to_state=ON)
def send_critical_door_open_notif(state_change: StateChangeEvent) -> None:
    now = local_now()
    nobody_home = not person.marshall.is_home and not person.emily.is_home
    is_nighttime = now.hour < 5

    just_got_home = (
        person.marshall.is_home and now - person.marshall.last_changed < timedelta(minutes=5)
    ) or (person.emily.is_home and now - person.emily.last_changed < timedelta(minutes=5))

    if nobody_home or (is_nighttime and not just_got_home):
        door = state_change.entity_id.resolve_entity()
        friendly_name = door.friendly_name.replace(" Sensor", "")
        time = now.strftime("%-I:%M %p")

        target: list[Person] = [person.marshall, person.emily] if nobody_home else [person.marshall]

        Notif(
            title="⚠️ Door Opened ⚠️",
            message=f"{friendly_name} opened at {time}",
            priority=Notif.Priority.CRITICAL,
        ).send(*target)
