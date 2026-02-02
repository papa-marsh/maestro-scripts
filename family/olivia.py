from maestro.registry import person, switch
from maestro.triggers import event_fired_trigger
from scripts.common.event_type import EventType


@event_fired_trigger(EventType.OLIVIA_ASLEEP)
def sound_machine_on() -> None:
    if not person.emily.is_home:
        return

    switch.olivias_sound_machine.turn_on()


@event_fired_trigger(EventType.OLIVIA_AWAKE)
def sound_machine_off() -> None:
    switch.olivias_sound_machine.turn_off()
