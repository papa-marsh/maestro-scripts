from datetime import date

from maestro.registry import maestro
from maestro.triggers import HassEvent, MaestroEvent, cron_trigger, hass_trigger, maestro_trigger


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
@cron_trigger(hour=0)
def set_sidebar_text() -> None:
    today = date.today().strftime("%A")
    sidebar_text = f"""
        <li>Happy {today}!</li>
        <li>‎</li>
    """

    maestro.cast_sidebar_text.state_manager.post_hass_entity(
        entity_id=maestro.cast_sidebar_text.id,
        state=sidebar_text,
        attributes={},
    )
