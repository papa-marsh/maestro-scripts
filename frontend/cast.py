from time import sleep

from maestro.domains import MediaPlayer
from maestro.integrations import Domain, RedisClient
from maestro.registry import media_player
from maestro.triggers import cron_trigger

NEST_DISPLAYS: list[MediaPlayer] = [
    media_player.office_display,
    media_player.living_room_display,
    media_player.kitchen_display,
]

CAST_LOCK_KEY = "cast_lock"


def call_cast_command(display: MediaPlayer) -> None:
    display.state_manager.hass_client.perform_action(
        domain=Domain.SHELL_COMMAND,
        action=f"cast_to_{display.id.entity}",
        entity_id=display.id,
    )


@cron_trigger("*/10 * * * *")
def cast_to_displays(force_reset: bool = False) -> None:
    with RedisClient().lock(CAST_LOCK_KEY, timeout_seconds=180, exit_if_owned=True):
        for display in NEST_DISPLAYS:
            if force_reset and display.state == "on":
                display.turn_off()
                sleep(5)
            if force_reset or display.state == "off":
                display.turn_on()
                sleep(5)
                display.turn_off()
                sleep(5)
                call_cast_command(display)
                sleep(30)
