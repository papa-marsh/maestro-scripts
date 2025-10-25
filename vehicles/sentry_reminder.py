from maestro.integrations import RedisClient
from maestro.registry import lock, person, zone
from maestro.triggers import state_change_trigger
from maestro.utils import IntervalSeconds, Notif, local_now

from .common import Tess


@state_change_trigger(lock.tess_doors, to_state="locked")
def turn_sentry_off_reminder() -> None:
    """Reminder to turn off Sentry at DePrees with a 30 min debounce"""
    sentry_off = Tess.sentry_mode.state == "off"
    at_deprees = Tess.location_tracker.state == zone.the_deprees.friendly_name
    if sentry_off or not at_deprees:
        return

    redis_key = "sentry_off_reminder_last_sent"
    redis_client = RedisClient()
    if redis_client.get(redis_key):
        return

    Notif(
        title="Sentry Mode On",
        message="Consider turning Sentry Mode off to conserve battery",
        tag="turn_sentry_off_reminder",
    ).send(person.marshall)

    redis_client.set(
        key=redis_key,
        value=local_now().isoformat(),
        ttl_seconds=IntervalSeconds.THIRTY_MINUTES,
    )
