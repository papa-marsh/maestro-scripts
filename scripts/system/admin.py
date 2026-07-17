from maestro.integrations import NotifActionEvent
from maestro.triggers import event_fired_trigger, notif_action_trigger
from maestro.utils import Notif, log

from registry import person
from scripts.common.event_type import EventType

ADMIN_EVENT_NOTIF_TAG = "admin_event"
FIRE_ACTION_PREFIX = "admin_fire_"

# Events that can't be fired standalone (recursive, or require event data)
EXCLUDED_EVENT_TYPES = frozenset({EventType.ADMIN_EVENT, EventType.MAESTRO_UI_EVENT})


@event_fired_trigger(EventType.ADMIN_EVENT)
def handle_admin_event() -> None:
    """Send Marshall an actionable notification enumerating all manually fireable events"""
    actions = [
        Notif.build_action(
            name=f"{FIRE_ACTION_PREFIX}{event_type}",
            title=event_type.replace("_", " ").title(),
        )
        for event_type in EventType
        if event_type not in EXCLUDED_EVENT_TYPES
    ]

    Notif(
        title="Admin Event",
        message="Long-press to fire event",
        actions=actions,
        tag=ADMIN_EVENT_NOTIF_TAG,
    ).send(person.marshall)


def fire_admin_event(notif_action: NotifActionEvent) -> None:
    """Fire the event selected from the admin notification, on behalf of whoever selected it"""
    event_type = EventType(notif_action.name.removeprefix(FIRE_ACTION_PREFIX))
    event_data = {"user_id": notif_action.user_id} if notif_action.user_id else {}

    log.info("Firing admin-selected event", event_type=event_type, **event_data)
    person.marshall.state_manager.hass_client.fire_event(event_type, **event_data)


# Register fire_admin_event under a unique notif action name per fireable event type
for _event_type in EventType:
    if _event_type not in EXCLUDED_EVENT_TYPES:
        notif_action_trigger(f"{FIRE_ACTION_PREFIX}{_event_type}")(fire_admin_event)
