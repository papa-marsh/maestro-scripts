from maestro.integrations import EntityId, StateChangeEvent, StateManager
from maestro.registry import maestro
from maestro.triggers import MaestroEvent, maestro_trigger, state_change_trigger
from maestro.utils.dates import local_now

from .common import Nyx, Tess


@maestro_trigger(MaestroEvent.STARTUP)
def initialize_complication_entities() -> None:
    state_manager = StateManager()

    for vehicle in (Nyx, Tess):
        state_manager.create_hass_entity(
            entity_id=EntityId(vehicle.watch_complication_id),
            state=local_now().isoformat(),
            attributes={
                "leading": "",
                "outer": "",
                "trailing": "",
                "gauge": 1.0,
            },
        )


# @state_change_trigger(Nyx.battery, Nyx.lock, Nyx.charger, Tess.battery, Tess.lock, Tess.charger)
# def update_watch_complication(state_change: StateChangeEvent) -> None:
#     nyx_entities = [Nyx.battery.id, Nyx.lock.id, Nyx.charger.id]
#     vehicle = Nyx if state_change.entity_id in nyx_entities else Tess

#     maestro.
