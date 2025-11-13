from maestro.domains.media_player import MediaPlayer
from maestro.integrations import Domain, EntityId


class SonosSpeaker(MediaPlayer):
    group_members: list[str]

    def join(self, members: list[EntityId]) -> None:
        self.perform_action("join", group_members=members)

    def unjoin(self) -> None:
        self.perform_action("unjoin")

    def snapshot(self, with_group: bool = False) -> None:
        self.state_manager.hass_client.perform_action(
            domain=Domain.SONOS,
            action="snapshot",
            entity_id=self.id,
            with_group=with_group,
        )

    def restore(self, with_group: bool = False) -> None:
        self.state_manager.hass_client.perform_action(
            domain=Domain.SONOS,
            action="restore",
            entity_id=self.id,
            with_group=with_group,
        )
