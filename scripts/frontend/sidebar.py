from datetime import date

from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    hass_trigger,
    maestro_trigger,
    state_change_trigger,
)

from registry import maestro, sun


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
@state_change_trigger(sun.sun)
def set_sidebar_text() -> None:
    today = date.today().strftime("%A")

    if sun.sun.is_above_horizon:
        sun_action = "sets"
        sun_time = sun.sun.next_setting.strftime("%-I:%M %p")
    else:
        sun_action = "rises"
        sun_time = sun.sun.next_rising.strftime("%-I:%M %p")

    sidebar_text = f"""
        <li>Happy {today}!</li>
        <li>The sun {sun_action} at {sun_time}.</li>
    """

    maestro.cast_sidebar_text.state_manager.post_hass_entity(
        entity_id=maestro.cast_sidebar_text.id,
        state=sidebar_text,
        attributes={},
    )
