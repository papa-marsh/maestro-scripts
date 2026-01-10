from maestro.integrations import StateChangeEvent
from maestro.registry import media_player
from maestro.triggers import cron_trigger, state_change_trigger
from scripts.custom_domains.sonos_speaker import SonosSpeaker

MAIN_SPEAKERS: list[SonosSpeaker] = [
    media_player.living_room,
    media_player.craft_room,
    media_player.front_room,
    media_player.portable,
]
ALL_SPEAKERS: list[SonosSpeaker] = [
    *MAIN_SPEAKERS,
    media_player.basement,
    media_player.office,
]


@cron_trigger(hour=3)
def reset_speakers() -> None:
    for speaker in ALL_SPEAKERS:
        speaker.pause()
        speaker.unmute()

    for speaker in MAIN_SPEAKERS[:-1]:
        speaker.set_volume(0.3)

    media_player.portable.set_volume(0.15)
    media_player.basement.set_volume(0.4)
    media_player.office.set_volume(0.25)
    media_player.living_room_tv.set_volume(0.1)


@state_change_trigger(*MAIN_SPEAKERS, to_state="playing")
def group_speakers(state_change: StateChangeEvent) -> None:
    target = state_change.entity_id.resolve_entity()
    if not isinstance(target, SonosSpeaker):
        raise TypeError

    if all(speaker.id in target.group_members for speaker in MAIN_SPEAKERS):
        return

    target.join(MAIN_SPEAKERS)
