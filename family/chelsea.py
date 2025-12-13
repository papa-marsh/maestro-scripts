from datetime import timedelta

from maestro.registry import binary_sensor, person
from maestro.triggers import cron_trigger
from maestro.utils import Notif, local_now


@cron_trigger(hour=8)
@cron_trigger(hour=20)
def feed_chelsea_reminder() -> None:
    now = local_now()
    if binary_sensor.chelsea_cabinet_sensor.last_changed > now - timedelta(hours=1):
        return

    Notif(
        title="Feed Beth",
        message=f"Don't forget Chelsea's {'breakfast' if now.hour < 12 else 'dinner'}",
        tag="feed_chelsea",
        priority=Notif.Priority.TIME_SENSITIVE,
    ).send(person.marshall, person.emily)
