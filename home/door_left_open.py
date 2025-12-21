from datetime import timedelta

from maestro.domains import OFF, ON, UNAVAILABLE, BinarySensor, Cover
from maestro.integrations import EntityId, NotifActionEvent, StateChangeEvent
from maestro.registry import binary_sensor, cover, person
from maestro.triggers import notif_action_trigger, state_change_trigger
from maestro.utils import JobScheduler, Notif, format_duration, local_now

PROCESS_ID_PREFIX = "door_left_open"
SILENCE_NOTIF_ACTION_ID = "silence_door_notif"

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


@state_change_trigger(*EXTERIOR_DOORS, to_state=ON)
@state_change_trigger(*GARAGE_STALLS, to_state="open")
def schedule_notifications(state_change: StateChangeEvent) -> None:
    if state_change.old.state == UNAVAILABLE:
        return

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


def send_notifications(door: BinarySensor | Cover, duration: timedelta) -> None:
    friendly_name = door.friendly_name.replace(" Sensor", "")

    silence_action = Notif.build_action(
        name=SILENCE_NOTIF_ACTION_ID,
        title="Silence",
    )

    Notif(
        title="Door Left Open",
        message=f"{friendly_name} has been open for {format_duration(duration)}",
        group=PROCESS_ID_PREFIX,
        tag=get_process_id(door.id),
        actions=[silence_action],
        action_data={"entity_id": door.id},
    ).send(person.marshall, person.emily)


@state_change_trigger(*EXTERIOR_DOORS, to_state=OFF)
@state_change_trigger(*GARAGE_STALLS, to_state="closed")
def door_closed_cancel_notifs(state_change: StateChangeEvent) -> None:
    cancel_notifications(state_change.entity_id)


@notif_action_trigger(SILENCE_NOTIF_ACTION_ID)
def silence_notif_action_called(notif_action: NotifActionEvent) -> None:
    entity_id = notif_action.action_data["entity_id"]
    cancel_notifications(entity_id)


def cancel_notifications(entity_id: EntityId) -> None:
    scheduler = JobScheduler()
    for time in NOTIFICATION_TIMES:
        job_id = get_job_id(entity_id, time)
        scheduler.cancel_job(job_id)
