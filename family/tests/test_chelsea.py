from datetime import timedelta

from maestro.domains import OFF
from maestro.integrations import Domain
from maestro.registry import binary_sensor, person
from maestro.testing import MaestroTest
from maestro.utils import local_now

from .. import chelsea


def test_feed_chelsea_reminder(mt: MaestroTest) -> None:
    # Notif doesn't send after recent state change
    mt.set_state(
        entity=binary_sensor.chelsea_cabinet_sensor,
        state=OFF,
        attributes={
            "last_changed": local_now() - timedelta(minutes=30),
        },
    )
    chelsea.feed_chelsea_reminder()
    mt.assert_action_not_called(Domain.NOTIFY, person.marshall.notify_action_name)
    mt.assert_action_not_called(Domain.NOTIFY, person.emily.notify_action_name)

    # Notif sends to both people if no recent state change
    mt.set_state(
        entity=binary_sensor.chelsea_cabinet_sensor,
        state=OFF,
        attributes={
            "last_changed": local_now() - timedelta(hours=8),
        },
    )
    chelsea.feed_chelsea_reminder()
    mt.assert_action_called(Domain.NOTIFY, person.marshall.notify_action_name)
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)
