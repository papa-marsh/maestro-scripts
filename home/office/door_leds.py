from maestro.registry import switch
from maestro.triggers import event_fired_trigger


@event_fired_trigger("office_leds")
def toggle_office_leds() -> None:
    switch.office_door_led.toggle()
