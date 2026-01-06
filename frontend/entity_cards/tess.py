from dataclasses import asdict

from maestro.integrations import EntityId
from maestro.registry import maestro
from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    hass_trigger,
    maestro_trigger,
    state_change_trigger,
)
from scripts.frontend.common.entity_card import EntityCardAttributes
from scripts.frontend.common.icons import Icon
from scripts.vehicles.common import Tess

card = maestro.entity_card_1


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize_card() -> None:
    attributes = EntityCardAttributes(
        title="Tess",
        icon=Icon.CAR_ELECTRIC_OUTLINE,
    )
    card.state_manager.initialize_hass_entity(
        entity_id=card.id,
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )

    card.state_manager.initialize_hass_entity(
        entity_id=EntityId("maestro.entity_card_2"),
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )
    card.state_manager.initialize_hass_entity(
        entity_id=EntityId("maestro.entity_card_3"),
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )
    card.state_manager.initialize_hass_entity(
        entity_id=EntityId("maestro.entity_card_4"),
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )
    card.state_manager.initialize_hass_entity(
        entity_id=EntityId("maestro.entity_card_5"),
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )
    card.state_manager.initialize_hass_entity(
        entity_id=EntityId("maestro.entity_card_6"),
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )


# @state_change_trigger(Tess.climate, Tess.parked, Tess.software_update)
# def set_state() -> None:
#     if not Tess.parked.is_on:
#         card.state = "Driving"
#         card.icon =
