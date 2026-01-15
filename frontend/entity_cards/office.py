from dataclasses import asdict
from datetime import datetime

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
from maestro.utils import IntervalSeconds
from scripts.common.event_type import UIEvent, ui_event_trigger
from scripts.common.finance import FinnhubResponse, get_stock_quote
from scripts.frontend.common.entity_card import EntityCardAttributes, RowColor
from scripts.frontend.common.icons import Icon
from scripts.home.office.meetings import toggle_meeting_active

card = maestro.entity_card_4

STOCK_LAST_UPDATED_PREFIX = "stock_last_updated"


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize_card() -> None:
    attributes = EntityCardAttributes(
        title="Office",
        icon=Icon.CLOUD,
    )
    card.state_manager.initialize_hass_entity(
        entity_id=card.id,
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )
    card.update(title=attributes.title, row_2_icon=Icon.FINANCE, row_3_icon=Icon.CLOUD_OUTLINE)


@state_change_trigger(maestro.meeting_active)
def set_state(state_change: StateChangeEvent) -> None:
    if state_change.new.state == ON:
        active = True
        state = "Busy"
        icon = Icon.HEADSET
    else:
        active = False
        state = "Available"
        icon = Icon.CLOUD

    card.update(state=state, active=active, icon=icon)


@state_change_trigger(
    sensor.office_ambient_sensor_temperature,
    sensor.office_ambient_sensor_humidity,
    switch.space_heater,
)
def set_row_1() -> None:
    if sensor.office_ambient_sensor_temperature.state in [UNKNOWN, UNAVAILABLE]:
        card.update(row_1_value="Offline", row_1_icon=Icon.THERMOMETER_OFF)
        return

    temperature = float(sensor.office_ambient_sensor_temperature.state)
    humidity = float(sensor.office_ambient_sensor_humidity.state)

    value = f"{temperature:.0f}° · {humidity:.0f}%"
    icon = Icon.RADIATOR if switch.space_heater.is_on else Icon.THERMOMETER_WATER
    card.update(row_1_value=value, row_1_icon=icon)


def resolve_quote_display(quote: FinnhubResponse) -> tuple[str, RowColor]:
    price = quote.c
    change_percent = quote.dp * 100
    plus_sign = "+" if quote.dp >= 0 else ""
    value = f"${price:.0f} ({plus_sign}{change_percent:.0f}%)"
    color = (
        RowColor.GREEN
        if change_percent > 5
        else RowColor.RED
        if change_percent < -5
        else RowColor.DEFAULT
    )
    return value, color


@cron_trigger("* 9-16 * * 1-5")
def set_row_2() -> None:
    redis = card.state_manager.redis_client
    last_updated_key = redis.build_key(STOCK_LAST_UPDATED_PREFIX, "spy")
    last_updated_iso = redis.get(last_updated_key)

    quote = get_stock_quote("SPY")
    quote_timestamp = datetime.fromtimestamp(quote.t)

    if last_updated_iso and quote_timestamp <= datetime.fromisoformat(last_updated_iso):
        return

    value, color = resolve_quote_display(quote)

    card.update(row_2_value=value, row_2_color=color)

    card.state_manager.redis_client.set(
        key=last_updated_key,
        value=quote_timestamp.isoformat(),
        ttl_seconds=IntervalSeconds.ONE_WEEK,
    )


@cron_trigger("* 9-16 * * 1-5")
def set_row_3() -> None:
    redis = card.state_manager.redis_client
    last_updated_key = redis.build_key(STOCK_LAST_UPDATED_PREFIX, "net")
    last_updated_iso = redis.get(last_updated_key)

    quote = get_stock_quote("NET")
    quote_timestamp = datetime.fromtimestamp(quote.t)

    if last_updated_iso and quote_timestamp <= datetime.fromisoformat(last_updated_iso):
        return

    value, color = resolve_quote_display(quote)

    card.update(row_2_value=value, row_2_color=color)

    card.state_manager.redis_client.set(
        key=last_updated_key,
        value=quote_timestamp.isoformat(),
        ttl_seconds=IntervalSeconds.ONE_WEEK,
    )


@cron_trigger(hour=2)
def reset_stock_rows() -> None:
    card.update(
        row_2_value=card.row_2_value.split(" ")[1],
        row_2_color=RowColor.DEFAULT,
        row_3_value=card.row_3_value.split(" ")[1],
        row_3_color=RowColor.DEFAULT,
    )


@cron_trigger(hour=8, minute=30, day_of_week=[0, 1, 2, 3, 4])
def daily_review_reminder() -> None:
    card.blink = True


@ui_event_trigger(UIEvent.ENTITY_CARD_4_TAP)
def handle_tap() -> None:
    if card.blink:
        card.blink = False
        return

    toggle_meeting_active()


@ui_event_trigger(UIEvent.ENTITY_CARD_4_HOLD)
def handle_hold() -> None:
    if switch.space_heater.is_on:
        switch.space_heater.turn_off()
    else:
        switch.space_heater.turn_on()
