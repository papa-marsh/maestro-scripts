from maestro.registry import person, sensor
from maestro.triggers import cron_trigger
from maestro.utils import Notif


@cron_trigger(hour=8)
def check_cloud_backup_state() -> None:
    if sensor.backup_state.state != "backed_up":
        Notif(
            title="Cloud Backup Failed",
            message="Google Drive backup appears to have failed - Check add-on",
        ).send(person.marshall)
