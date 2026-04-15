from datetime import timedelta

from maestro.integrations import RedisClient
from maestro.registry import input_boolean, person, switch
from maestro.utils import IntervalSeconds, JobScheduler, local_now
from scripts.custom_domains.sprinkler_zone import SprinklerZone


class SprinklerController:
    redis: RedisClient
    scheduler: JobScheduler

    zone_1 = switch.rain_bird_sprinkler_1
    zone_2 = switch.rain_bird_sprinkler_2
    zone_3 = switch.rain_bird_sprinkler_3
    zone_4 = switch.rain_bird_sprinkler_4
    zone_5 = switch.rain_bird_sprinkler_5

    all_zones: tuple[SprinklerZone, ...] = (zone_1, zone_2, zone_3, zone_4, zone_5)

    ZONE_RUN_TIME_CACHE_PREFIX = "sprinkler_run_time_zone_"
    RUN_ZONE_JOB_ID_PREFIX = "sprinkler_run_zone_"

    def __init__(
        self,
        redis_client: RedisClient | None = None,
        scheduler: JobScheduler | None = None,
    ) -> None:
        self.redis = redis_client or RedisClient()
        self.scheduler = scheduler or JobScheduler()

    def stop_all(self) -> None:
        for zone in self.all_zones:
            job_id = self.build_zone_run_job_id(zone)
            self.scheduler.cancel_job(job_id)
            zone.turn_off()

    @property
    def skip_next(self) -> bool:
        return input_boolean.sprinklers_skip_next.is_on

    @skip_next.setter
    def skip_next(self, value: bool) -> None:
        if value:
            input_boolean.sprinklers_skip_next.turn_on()
        else:
            input_boolean.sprinklers_skip_next.turn_off()

    def get_zone_run_time(self, zone: SprinklerZone) -> int:
        key = self.build_run_time_cache_key(zone)
        run_time_string = self.redis.get(key)
        if run_time_string is None:
            raise ValueError(f"No run_time found for key {key}")

        return int(run_time_string)

    def set_zone_run_time(self, zone: SprinklerZone, minutes: int) -> None:
        self.redis.set(
            key=self.build_run_time_cache_key(zone),
            value=str(minutes),
            ttl_seconds=IntervalSeconds.TWO_WEEKS,
        )

    def run_program(self) -> None:
        if input_boolean.sprinklers_running.is_on:
            person.marshall.notify("Can't run program when sprinklers are already running")
            return

        person.marshall.notify("Starting sprinkler program")
        start_time = local_now() + timedelta(seconds=2)

        for zone in self.all_zones:
            run_time = min(self.get_zone_run_time(zone), 30)
            self.scheduler.schedule_job(
                run_time=start_time,
                func=zone.run,
                func_params={"minutes": run_time},
                job_id=self.build_zone_run_job_id(zone),
            )
            start_time = start_time + timedelta(minutes=run_time, seconds=5)

    @classmethod
    def build_run_time_cache_key(cls, zone: SprinklerZone) -> str:
        prefix = cls.ZONE_RUN_TIME_CACHE_PREFIX
        zone_number = str(zone.zone)

        return prefix + zone_number

    @classmethod
    def build_zone_run_job_id(cls, zone: SprinklerZone) -> str:
        prefix = cls.RUN_ZONE_JOB_ID_PREFIX
        zone_number = str(zone.zone)

        return prefix + zone_number
