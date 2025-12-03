from maestro.domains import HOME, Fan
from maestro.registry import fan, person
from maestro.triggers import cron_trigger, state_change_trigger


@cron_trigger(hour=23)
def air_purifier_on() -> None:
    fan.office_purifier.set_speed(Fan.Speed.MEDIUM)


@cron_trigger(hour=5)
def air_purifier_off() -> None:
    fan.office_purifier.turn_off()


@state_change_trigger(person.marshall, person.emily)
def air_purifier_on_while_away() -> None:
    if person.marshall.state != HOME and person.emily.state != HOME:
        fan.office_purifier.turn_on()
    else:
        fan.office_purifier.turn_off()
