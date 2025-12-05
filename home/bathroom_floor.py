from datetime import timedelta

from maestro.domains import Person
from maestro.integrations import FiredEvent, StateChangeEvent
from maestro.registry import climate, person
from maestro.triggers import event_fired_trigger, state_change_trigger
from maestro.utils import JobScheduler, Notif, format_duration, local_now
from scripts.config.secrets import USER_ID_TO_PERSON
from scripts.custom_domains import BathroomFloor

HEAT_TEMPERATURE = 85
HEAT_DURATION = timedelta(minutes=90)
AUTO_SHUTOFF_TIME = timedelta(hours=3)

TEMPERATURE_CHECK_JOB_ID = "bathroom_floor_check_temp"
TURN_OFF_HEAT_JOB_ID = "bathroom_floor_turn_off_heat"
AUTO_SHUTOFF_JOB_ID = "bathroom_floor_auto_shutoff"


@event_fired_trigger("bathroom_floor")
def heat_bathroom_floor(event: FiredEvent) -> None:
    now = local_now()
    caller = USER_ID_TO_PERSON[str(event.user_id)]

    climate.bathroom_floor_thermostat.set_temperature(HEAT_TEMPERATURE)

    scheduler = JobScheduler()

    scheduler.schedule_job(
        run_time=now + timedelta(minutes=1),
        func=check_floor_temp,
        func_params={"caller": caller},
        job_id=TEMPERATURE_CHECK_JOB_ID,
    )

    scheduler.schedule_job(
        run_time=now + HEAT_DURATION,
        func=reset_floor_to_auto,
        job_id=TURN_OFF_HEAT_JOB_ID,
    )


def reset_floor_to_auto() -> None:
    climate.bathroom_floor_thermostat.set_preset_mode(BathroomFloor.PresetMode.RUN_SCHEDULE)


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


@state_change_trigger(climate.bathroom_floor_thermostat)
def bathroom_floor_timeout_handler(state_change: StateChangeEvent) -> None:
    scheduler = JobScheduler()

    if state_change.new.state == BathroomFloor.HVACMode.AUTO:
        scheduler.cancel_job(AUTO_SHUTOFF_JOB_ID)
        return

    def reset_after_timeout() -> None:
        duration = format_duration(AUTO_SHUTOFF_TIME)
        Notif(
            title="Bathroom Floor Still On",
            message=f"Auto shutoff triggered for bathroom floor after {duration}",
            priority=Notif.Priority.TIME_SENSITIVE,
        ).send(person.marshall)
        reset_floor_to_auto()

    scheduler.schedule_job(
        run_time=local_now() + AUTO_SHUTOFF_TIME,
        func=reset_after_timeout,
        job_id=AUTO_SHUTOFF_JOB_ID,
    )
