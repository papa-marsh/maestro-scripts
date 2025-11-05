from datetime import timedelta

from maestro.domains.person import Person
from maestro.integrations.home_assistant.types import FiredEvent
from maestro.registry import climate
from maestro.triggers import event_fired_trigger
from maestro.utils.dates import IntervalSeconds, local_now
from maestro.utils.push import Notif
from maestro.utils.scheduler import JobScheduler
from scripts.config.secrets import USER_ID_TO_PERSON

HEAT_DURATION = timedelta(seconds=IntervalSeconds.NINETY_MINUTES)
HEAT_TEMPERATURE = 85

TEMPERATURE_CHECK_JOB_ID = "bathroom_floor_check_temp"
TURN_OFF_HEAT_JOB_ID = "bathroom_floor_turn_off_heat"


@event_fired_trigger("bathroom_floor")
def heat_bathroom_floor(event: FiredEvent) -> None:
    now = local_now()
    caller = USER_ID_TO_PERSON[str(event.user_id)]

    climate.bathroom_floor_thermostat.set_temperature(85)

    scheduler = JobScheduler()

    scheduler.schedule_job(
        run_time=now + timedelta(minutes=1),
        func=check_floor_temp,
        func_params={"caller": caller},
        job_id=TEMPERATURE_CHECK_JOB_ID,
    )

    scheduler.schedule_job(
        run_time=now + HEAT_DURATION,
        func=check_floor_temp,
        func_params={"caller": caller},
        job_id=TEMPERATURE_CHECK_JOB_ID,
    )


def reset_floor_to_auto() -> None:
    bathroom_floor = climate.bathroom_floor_thermostat
    bathroom_floor.set_preset_mode(bathroom_floor.PresetMode.RUN_SCHEDULE)


def check_floor_temp(caller: Person) -> None:
    current_temp = climate.bathroom_floor_thermostat.current_temperature
    ready_threshold = HEAT_TEMPERATURE - 5

    if current_temp < ready_threshold:
        JobScheduler().schedule_job(
            run_time=local_now() + timedelta(minutes=1),
            func=check_floor_temp,
            func_params={"caller": caller},
            job_id=TEMPERATURE_CHECK_JOB_ID,
        )
        return

    Notif(
        title="Bathroom Floor Ready",
        message=f"The bathroom floor is a nice warm {current_temp}°",
        priority=Notif.Priority.TIME_SENSITIVE,
        tag="heat_bathroom_floor",
    ).send(caller)
