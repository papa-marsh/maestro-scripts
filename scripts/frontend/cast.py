from concurrent.futures import ThreadPoolExecutor
from time import sleep

from catt.controllers import setup_cast  # type:ignore[import-untyped]
from maestro.domains import MediaPlayer
from maestro.integrations import RedisClient
from maestro.triggers import cron_trigger
from maestro.utils import log

from registry import media_player

NEST_DISPLAYS: list[tuple[MediaPlayer, str]] = [
    (media_player.office_display, "192.168.0.125"),
    (media_player.living_room_display, "192.168.0.143"),
    (media_player.kitchen_display, "192.168.0.127"),
]

CAST_URL = "http://192.168.0.107:8123/lovelace-cast/overview"
CAST_LOCK_KEY_PREFIX = "cast_lock_"
CAST_TIMEOUT_SECONDS = 60


def execute_cast(ip_address: str) -> None:
    cast_controller = setup_cast(
        ip_address,
        controller="dashcast",
        action="load_url",
        prep="app",
    )
    cast_controller.load_url(CAST_URL)


def call_cast_command(display: MediaPlayer, ip_address: str) -> None:
    lock_key = CAST_LOCK_KEY_PREFIX + display.id.entity
    with RedisClient().lock(lock_key, timeout_seconds=100, exit_if_owned=True):
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            executor.submit(execute_cast, ip_address).result(timeout=CAST_TIMEOUT_SECONDS)
        except TimeoutError:
            log.error(
                "Timed out while attempting to cast",
                target=display.id,
                timeout_seconds=CAST_TIMEOUT_SECONDS,
            )
        except Exception:
            log.exception("Exception raised while attempting to cast", target=display.id)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)


@cron_trigger("*/10 * * * *")
def cast_to_displays() -> None:
    for display, ip_address in NEST_DISPLAYS:
        call_cast_command(display, ip_address)
        sleep(90)
