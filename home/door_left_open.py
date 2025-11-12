from datetime import timedelta

from maestro.domains import BinarySensor, Cover
from maestro.integrations import EntityId, StateChangeEvent
from maestro.registry import binary_sensor, cover, person
from maestro.triggers import state_change_trigger
from maestro.utils import JobScheduler, Notif, format_duration, local_now

PROCESS_ID_PREFIX = "door_left_open"

EXTERIOR_DOORS: list[BinarySensor] = [
    binary_sensor.front_door_sensor,
    binary_sensor.garage_door_sensor,
    binary_sensor.service_door_sensor,
    binary_sensor.slider_door_sensor,
]
GARAGE_STALLS: list[Cover] = [cover.east_stall, cover.west_stall]

NOTIFICATION_TIMES: list[timedelta] = [
    timedelta(minutes=10),
    timedelta(minutes=30),
    timedelta(minutes=60),
    timedelta(minutes=120),
]


def get_process_id(entity_id: EntityId) -> str:
    return f"{PROCESS_ID_PREFIX}_{entity_id.entity}"


def get_job_id(entity_id: EntityId, time: timedelta) -> str:
    return f"{get_process_id(entity_id)}_{int(time.total_seconds())}"


@state_change_trigger(*EXTERIOR_DOORS, to_state="on")
def schedule_notifications(state_change: StateChangeEvent) -> None:
    scheduler = JobScheduler()
    now = local_now()
    door = state_change.entity_id.resolve_entity()

    for time in NOTIFICATION_TIMES:
        job_id = get_job_id(entity_id=state_change.entity_id, time=time)
        scheduler.schedule_job(
            run_time=now + time,
            func=send_notifications,
            func_params={"door": door, "duration": time},
            job_id=job_id,
        )


@state_change_trigger(*EXTERIOR_DOORS, to_state="off")
def cancel_notifications(state_change: StateChangeEvent) -> None:
    scheduler = JobScheduler()

    for time in NOTIFICATION_TIMES:
        job_id = get_job_id(entity_id=state_change.entity_id, time=time)
        scheduler.cancel_job(job_id)


def send_notifications(door: BinarySensor, duration: timedelta) -> None:
    friendly_name = door.friendly_name.replace(" Sensor", "")

    silence_action = Notif.build_action(
        name=get_process_id(door.id),
        title="Silence",
    )

    Notif(
        title="Door Left Open",
        message=f"The {friendly_name} has been open for {format_duration(duration)}",
        group=PROCESS_ID_PREFIX,
        tag=get_process_id(door.id),
        actions=[silence_action],
    ).send(person.marshall, person.emily)
