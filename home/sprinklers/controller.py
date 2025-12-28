from maestro.integrations import RedisClient
from maestro.registry import calendar, switch
from maestro.utils import IntervalSeconds, local_now
from scripts.custom_domains.sprinkler_zone import SprinklerZone


class SprinklerController:
    redis: RedisClient

    zone_1 = switch.rain_bird_sprinkler_1
    zone_2 = switch.rain_bird_sprinkler_2
    zone_3 = switch.rain_bird_sprinkler_3
    zone_4 = switch.rain_bird_sprinkler_4
    zone_5 = switch.rain_bird_sprinkler_5
    calendar = calendar.rain_bird_controller

    all_zones: tuple[SprinklerZone, ...] = (zone_1, zone_2, zone_3, zone_4, zone_5)
    skip_next_cache_key = "SKIP_NEXT_SPRINKLER_RUN"

    def __init__(self, redis_client: RedisClient | None = None) -> None:
        self.redis = redis_client or RedisClient()

    @classmethod
    def stop_all(cls) -> None:
        for zone in cls.all_zones:
            if zone.is_on:
                zone.turn_off()

    @property
    def skip_next(self) -> bool:
        skip_next = self.redis.get(self.skip_next_cache_key) is not None
        return skip_next

    @skip_next.setter
    def skip_next(self, value: bool) -> None:
        if value:
            self.redis.set(
                key=self.skip_next_cache_key,
                value=local_now().isoformat(),
                ttl_seconds=IntervalSeconds.TWO_WEEKS,
            )
        else:
            self.redis.delete(self.skip_next_cache_key)

    def run_program(self) -> None: ...

    def get_schedule(self) -> None: ...

    def update_schedule(self) -> None: ...
