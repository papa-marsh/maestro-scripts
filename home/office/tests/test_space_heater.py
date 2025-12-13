from maestro.domains import OFF, ON
from maestro.integrations import Domain
from maestro.registry import switch
from maestro.testing import MaestroTest

from .. import space_heater


def test_space_heater_toggling(mt: MaestroTest) -> None:
    # Auto off job gets scheduled when heater turns on
    mt.trigger_state_change(switch.space_heater, new=ON)
    mt.assert_job_scheduled(space_heater.AUTO_OFF_JOB_ID, space_heater.turn_off_space_heater)

    # Heater turning off cancels job
    mt.trigger_state_change(switch.space_heater, new=OFF)
    mt.assert_job_not_scheduled(space_heater.AUTO_OFF_JOB_ID)

    # Heater turns off when job runs
    space_heater.turn_off_space_heater()
    mt.assert_action_called(Domain.SWITCH, "turn_off", switch.space_heater.id)
