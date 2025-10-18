from maestro.registry import switch
from maestro.triggers import event_fired_trigger


@event_fired_trigger("olivia_asleep")
def sound_machine_on() -> None:
    switch.olivias_sound_machine.turn_on()


@event_fired_trigger("olivia_awake")
def sound_machine_off() -> None:
    switch.olivias_sound_machine.turn_off()
