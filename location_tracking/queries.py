from datetime import datetime

from maestro.domains import Person
from maestro.utils import IntervalSeconds

LAST_LEFT_HOME_KEY_PREFIX = "LAST_LEFT_HOME"
PREV_ARRIVAL_KEY_PREFIX = "PREV_ZONE_ARRIVAL"


def get_last_left_home(person: Person) -> datetime | None:
    redis = person.state_manager.redis_client
    last_left_home_key = redis.build_key(LAST_LEFT_HOME_KEY_PREFIX, person.id.entity)

    timestamp_string = redis.get(key=last_left_home_key)

    return datetime.fromisoformat(timestamp_string) if timestamp_string else None


def set_last_left_home(person: Person, value: datetime) -> None:
    redis = person.state_manager.redis_client
    last_left_home_key = redis.build_key(LAST_LEFT_HOME_KEY_PREFIX, person.id.entity)

    redis.set(
        key=last_left_home_key,
        value=value.isoformat(),
        ttl_seconds=IntervalSeconds.TWO_WEEKS,
    )


def get_last_zone_arrival(person: Person) -> datetime | None:
    redis = person.state_manager.redis_client
    prev_arrival_key = redis.build_key(PREV_ARRIVAL_KEY_PREFIX, person.id)

    timestamp_string = redis.get(key=prev_arrival_key)

    return datetime.fromisoformat(timestamp_string) if timestamp_string else None


def set_last_zone_arrival(person: Person, value: datetime) -> None:
    redis = person.state_manager.redis_client
    prev_arrival_key = redis.build_key(PREV_ARRIVAL_KEY_PREFIX, person.id)

    redis.set(
        key=prev_arrival_key,
        value=value.isoformat(),
        ttl_seconds=IntervalSeconds.TWO_WEEKS,
    )
