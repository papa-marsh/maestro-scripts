from maestro.domains import OFF, ON
from maestro.integrations import Domain
from maestro.registry import switch
from maestro.testing import MaestroTest

from .. import ellie


def test_toggle_butterfly_light(mt: MaestroTest) -> None:
    # Light turns on when sound machine turns off
    mt.trigger_state_change(switch.ellies_sound_machine, new=OFF)
    mt.assert_action_called(
        domain=Domain.SWITCH,
        action="turn_on",
        entity_id=switch.butterfly_night_light.id,
    )

    # Light turns off when sound machine turns on
    mt.trigger_state_change(switch.ellies_sound_machine, new=ON)
    mt.assert_action_called(
        domain=Domain.SWITCH,
        action="turn_off",
        entity_id=switch.butterfly_night_light.id,
    )
