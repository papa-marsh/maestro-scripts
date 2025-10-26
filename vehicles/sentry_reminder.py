from datetime import timedelta

from maestro.registry import person, zone
from maestro.triggers import state_change_trigger
from maestro.utils import JobScheduler, Notif, local_now

from .common import Tess

SENTRY_REMINDER_JOB_ID = "sentry_reminder_job_id"


@state_change_trigger(Tess.location, to_state=zone.the_deprees.friendly_name)
def sentry_reminder() -> None:
    """Reminder to turn off Sentry at the deprees after a 30 min debounce"""

    def send_reminder() -> None:
        if Tess.sentry_mode.state == "off":
            return

        Notif(
            title="Sentry Mode On",
            message="Consider turning Sentry Mode off to conserve battery",
            tag="turn_sentry_off_reminder",
        ).send(person.marshall)

    JobScheduler().schedule_job(
        run_time=local_now() + timedelta(minutes=30),
        func=send_reminder,
        job_id=SENTRY_REMINDER_JOB_ID,
    )


@state_change_trigger(Tess.location, from_state=zone.the_deprees.friendly_name)
def cancel_reminder() -> None:
    JobScheduler().cancel_job(SENTRY_REMINDER_JOB_ID)
