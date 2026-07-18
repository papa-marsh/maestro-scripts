from maestro.registry import RegistryManager
from maestro.triggers import cron_trigger


@cron_trigger(hour=5)
def daily_registry_prune() -> None:
    RegistryManager.prune()
