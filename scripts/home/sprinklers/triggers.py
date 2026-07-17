from datetime import datetime, timedelta

from maestro.domains import OFF, ON
from maestro.integrations import StateChangeEvent
from maestro.triggers import state_change_trigger
from maestro.utils import Notif, local_now

from custom_domains.sprinkler_zone import SprinklerZone
from registry import input_boolean, person
from scripts.common.event_type import UIEvent, ui_event_trigger
from scripts.home.sprinklers.controller import SprinklerController


@state_change_trigger(*SprinklerController.all_zones)
def set_running() -> None:
    if any(zone.is_on for zone in SprinklerController.all_zones):
        input_boolean.sprinklers_running.turn_on()
        return

    input_boolean.sprinklers_running.turn_off()


@ui_event_trigger(UIEvent.SPRINKLERS_RUN_PROGRAM)
def handle_run_program() -> None:
    SprinklerController().run_program()


@ui_event_trigger(UIEvent.SPRINKLERS_SKIP_NEXT)
def handle_skip_next() -> None:
    input_boolean.sprinklers_skip_next.toggle()


@ui_event_trigger(UIEvent.SPRINKLERS_STOP_ALL)
def handle_stop_all() -> None:
    SprinklerController().stop_all()


@state_change_trigger(*SprinklerController.all_zones, from_state=OFF, to_state=ON)
def cancel_auto_run_if_skipped() -> None:
    if not input_boolean.sprinklers_skip_next.is_on:
        return

    SprinklerController().stop_all()
    input_boolean.sprinklers_skip_next.turn_off()

    Notif(
        title="Sprinklers Skipped",
        message="The scheduled sprinkler program was skipped",
    ).send(person.marshall)


@state_change_trigger(*SprinklerController.all_zones, from_state=ON, to_state=OFF)
def cache_run_time(state_change: StateChangeEvent) -> None:
    if 7 <= local_now().hour < 22:
        return
    if sprinklers_skipped():
        return

    zone = state_change.entity_id.resolve_entity()
    if not isinstance(zone, SprinklerZone):
        raise TypeError

    start_time: datetime = state_change.old.attributes["last_changed"]
    end_time: datetime = state_change.new.attributes["last_changed"]
    run_time_seconds = (end_time - start_time).total_seconds()
    run_time_minutes = round(run_time_seconds / 60)

    SprinklerController().set_zone_run_time(zone, minutes=run_time_minutes)


def sprinklers_skipped() -> bool:
    """Return True if sprinklers are skipped or if `skip_next` was changed recently"""
    return (
        input_boolean.sprinklers_skip_next.is_on
        or local_now() - input_boolean.sprinklers_skip_next.last_changed < timedelta(minutes=60)
    )
