import os
from pathlib import Path

from maestro import MaestroApp


def _notify_action_mappings() -> dict[str, str]:
    return {
        mapping.split(":")[0]: mapping.split(":")[1]
        for mapping in os.environ.get("NOTIFY_ACTION_MAPPINGS", "").split(",")
        if ":" in mapping
    }


app = MaestroApp(
    hass_url=os.environ["HOME_ASSISTANT_URL"],
    hass_token=os.environ["HOME_ASSISTANT_TOKEN"],
    redis_host=os.environ["REDIS_HOST"],
    redis_port=int(os.environ["REDIS_PORT"]),
    db_url=os.environ.get("DATABASE_URL"),
    custom_domains_dir=Path("custom_domains"),
    timezone=os.environ.get("TIMEZONE", "America/New_York"),
    background_services=os.environ.get("MAESTRO_BACKGROUND_SERVICES", "true").lower() != "false",
    autopopulate_registry=os.environ.get("AUTOPOPULATE_REGISTRY", "").lower() in ("true", "1"),
    domain_ignore_list=tuple(
        domain for domain in os.environ.get("DOMAIN_IGNORE_LIST", "").split(",") if domain
    ),
    notify_action_mappings=_notify_action_mappings(),
    default_notif_sound=os.environ.get("DEFAULT_NOTIF_SOUND", "3rdParty_Failure_Haptic.caf"),
    critical_notif_sound=os.environ.get("CRITICAL_NOTIF_SOUND", "3rd_party_critical.caf"),
    default_notif_url=os.environ.get("DEFAULT_NOTIF_URL", "overview"),
)


@app.shell_context_processor
def make_shell_context() -> dict:
    """Pre-load common imports for the flask shell command"""
    from maestro.integrations.home_assistant.client import HomeAssistantClient
    from maestro.integrations.home_assistant.types import (
        AttributeId,
        EntityData,
        EntityId,
        StateChangeEvent,
        StateId,
    )
    from maestro.integrations.redis import RedisClient
    from maestro.integrations.state_manager import StateManager
    from maestro.registry.registry_manager import RegistryManager
    from maestro.triggers.sun import SolarEvent
    from maestro.triggers.trigger_manager import TriggerManager
    from maestro.utils import (
        IntervalSeconds,
        JobScheduler,
        Notif,
        local_now,
        resolve_timestamp,
    )

    hass = HomeAssistantClient()
    redis = RedisClient()
    sm = StateManager(hass_client=hass, redis_client=redis)
    rm = RegistryManager()
    triggers = TriggerManager.get_registry()

    print("Pre-loaded variables: hass, redis, sm, rm, triggers")

    return locals()
