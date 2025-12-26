from maestro.domains import Switch
from maestro.integrations import Domain


class SprinklerZone(Switch):
    def run(self, minutes: int) -> None:
        if minutes < 1 or minutes > 30:
            raise ValueError(f"Run duration must be between 1-30 minutes but got {minutes}")

        self.state_manager.hass_client.perform_action(
            domain=Domain.RAINBIRD,
            action="start_irrigation",
            entity_id=self.id,
            duration=minutes,
        )
