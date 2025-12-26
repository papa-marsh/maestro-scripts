from maestro.integrations import Domain
from maestro.registry import person, sensor
from maestro.testing import MaestroTest

from .. import backups


def test_check_cloud_backup_state(mt: MaestroTest) -> None:
    # Notif not sent when backup state is backed_up
    mt.set_state(sensor.backup_state, "backed_up")
    backups.check_cloud_backup_state()
    mt.assert_action_not_called(Domain.NOTIFY, person.marshall.notify_action_name)

    # Notif sent when backup state is not backed_up
    mt.set_state(sensor.backup_state, "failed")
    backups.check_cloud_backup_state()
    mt.assert_action_called(Domain.NOTIFY, person.marshall.notify_action_name)
