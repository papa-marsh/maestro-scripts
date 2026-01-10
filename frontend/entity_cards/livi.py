from dataclasses import asdict
from datetime import timedelta
from time import sleep

from maestro.registry import maestro
from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    cron_trigger,
    event_fired_trigger,
    hass_trigger,
    maestro_trigger,
)
from maestro.utils import format_duration, local_now
from scripts.common.event_type import EventType
from scripts.frontend.common.entity_card import EntityCardAttributes
from scripts.frontend.common.icons import Icon
from scripts.sleep_tracking.queries import get_awake_time, get_last_event

card = maestro.entity_card_5


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize_card() -> None:
    attributes = EntityCardAttributes(
        title="Livi",
        icon=Icon.BABY,
    )
    card.state_manager.initialize_hass_entity(
        entity_id=card.id,
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )
    card.update(
        title=attributes.title,
        row_1_icon=Icon.TIMER_OUTLINE,
        row_2_icon=Icon.CALENDAR_TODAY,
    )


@cron_trigger("* * * * *")
def update_card() -> None:
    last_sleep_event = get_last_event()
    awake: bool = last_sleep_event.wakeup
    duration: timedelta = local_now() - last_sleep_event.timestamp
    awake_time = get_awake_time()

    card.update(
        state="Awake" if awake else "Asleep",
        icon=Icon.BABY_BUGGY if awake else Icon.SLEEP,
        active=not awake,
        row_1_value=format_duration(duration),
        row_2_value=format_duration(awake_time),
    )


@event_fired_trigger(EventType.OLIVIA_ASLEEP)
@event_fired_trigger(EventType.OLIVIA_AWAKE)
def trigger_update() -> None:
    sleep(2)  # Let DB operations complete
    update_card()
