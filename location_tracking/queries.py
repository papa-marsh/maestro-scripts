from datetime import datetime

from maestro.utils import IntervalSeconds
from scripts.location_tracking.notifications import ZoneChangeEvent

LAST_LEFT_HOME_KEY_PREFIX = "LAST_LEFT_HOME"
PREV_ARRIVAL_KEY_PREFIX = "PREV_ZONE_ARRIVAL"


def get_last_left_home(event: ZoneChangeEvent) -> datetime | None:
    redis = event.person.state_manager.redis_client
    last_left_home_key = redis.build_key(LAST_LEFT_HOME_KEY_PREFIX, event.person.id)

    timestamp_string = redis.get(key=last_left_home_key)

    return datetime.fromisoformat(timestamp_string) if timestamp_string else None


def set_last_left_home(event: ZoneChangeEvent) -> None:
    redis = event.person.state_manager.redis_client
    last_left_home_key = redis.build_key(LAST_LEFT_HOME_KEY_PREFIX, event.person.id)

    redis.set(
        key=last_left_home_key,
        value=event.timestamp.isoformat(),
        ttl_seconds=IntervalSeconds.TWO_WEEKS,
    )


def get_last_zone_arrival(event: ZoneChangeEvent) -> datetime | None:
    redis = event.person.state_manager.redis_client
    prev_arrival_key = redis.build_key(PREV_ARRIVAL_KEY_PREFIX, event.person.id)

    timestamp_string = redis.get(key=prev_arrival_key)

    return datetime.fromisoformat(timestamp_string) if timestamp_string else None


def set_last_zone_arrival(event: ZoneChangeEvent) -> None:
    redis = event.person.state_manager.redis_client
    prev_arrival_key = redis.build_key(PREV_ARRIVAL_KEY_PREFIX, event.person.id)

    redis.set(
        key=prev_arrival_key,
        value=event.timestamp.isoformat(),
        ttl_seconds=IntervalSeconds.TWO_WEEKS,
    )
