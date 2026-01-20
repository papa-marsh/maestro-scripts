from dataclasses import asdict

from maestro.domains import ON, UNAVAILABLE, UNKNOWN
from maestro.integrations import StateChangeEvent
from maestro.registry import maestro, sensor, switch
from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    cron_trigger,
    hass_trigger,
    maestro_trigger,
    state_change_trigger,
)
from scripts.common.event_type import UIEvent, ui_event_trigger
from scripts.frontend.common.entity_card import EntityCardAttributes
from scripts.frontend.common.icons import Icon
from scripts.home.office.meetings import toggle_meeting_active

card = maestro.entity_card_6


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize_card() -> None:
    attributes = EntityCardAttributes(
        title="Hass",
        icon=Icon.RASPBERRY_PI,
    )
    card.state_manager.initialize_hass_entity(
        entity_id=card.id,
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )
    card.update(title=attributes.title)
