from datetime import timedelta

from maestro.registry import switch
from maestro.triggers import state_change_trigger
from maestro.utils import JobScheduler, local_now

AUTO_OFF_JOB_ID = "office_space_heater_auto_off"


def turn_off_space_heater() -> None:
    switch.space_heater.turn_off()


@state_change_trigger(switch.space_heater, from_state="off", to_state="on")
def space_heater_auto_off() -> None:
    two_hours_from_now = local_now() + timedelta(hours=2)
    JobScheduler().schedule_job(
        run_time=two_hours_from_now,
        func=turn_off_space_heater,
        job_id=AUTO_OFF_JOB_ID,
    )


@state_change_trigger(switch.space_heater, to_state="off")
def cancel_auto_off_job() -> None:
    JobScheduler().cancel_job(AUTO_OFF_JOB_ID)
