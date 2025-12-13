from maestro.domains.entity import HOME, OFF, ON
from maestro.integrations.home_assistant.domain import Domain
from maestro.registry import person, zone
from maestro.testing import MaestroTest
from scripts.vehicles.common import Tess

from .. import sentry_reminder


def test_reminder_job_gets_set_and_cancelled(maestro_test: MaestroTest) -> None:
    # Job gets scheduler when Tess arrives at the deprees
    maestro_test.trigger_state_change(
        Tess.location,
        old=HOME,
        new=zone.the_deprees.friendly_name,
    )
    maestro_test.assert_job_scheduled(sentry_reminder.SENTRY_REMINDER_JOB_ID)

    # Test job gets cancelled when Tess leaves
    maestro_test.trigger_state_change(
        Tess.location,
        old=zone.the_deprees.friendly_name,
        new=HOME,
    )
    maestro_test.assert_job_not_scheduled(sentry_reminder.SENTRY_REMINDER_JOB_ID)


def test_send_reminder_triggers_notif(maestro_test: MaestroTest) -> None:
    # Notif doesn't fire if sentry is on
    maestro_test.set_state(Tess.sentry_mode, ON)
    sentry_reminder.send_reminder()
    maestro_test.assert_action_not_called(Domain.NOTIFY, person.marshall.notify_action_name)

    # Notif fires if sentry is off
    maestro_test.set_state(Tess.sentry_mode, OFF)
    sentry_reminder.send_reminder()
    maestro_test.assert_action_called(Domain.NOTIFY, person.marshall.notify_action_name)
