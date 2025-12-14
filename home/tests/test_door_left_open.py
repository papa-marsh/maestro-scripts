from datetime import timedelta

from maestro.domains import OFF, ON, Cover
from maestro.integrations import Domain
from maestro.registry import binary_sensor, cover, person
from maestro.testing import MaestroTest

from .. import door_left_open

test_door = binary_sensor.front_door_sensor


def test_schedule_notifications(mt: MaestroTest) -> None:
    # Test that all doors schedule all notif jobs
    all_doors = door_left_open.EXTERIOR_DOORS + door_left_open.GARAGE_STALLS
    assert len(all_doors) == 6
    for door in door_left_open.EXTERIOR_DOORS:
        new_state = "open" if isinstance(door, Cover) else ON
        mt.trigger_state_change(door, new=new_state)
        for time in door_left_open.NOTIFICATION_TIMES:
            job_id = door_left_open.get_job_id(door.id, time)
            mt.assert_job_scheduled(job_id, door_left_open.send_notifications)


def test_send_notifications(mt: MaestroTest) -> None:
    # Notif sends to both people when function runs
    duration = timedelta(minutes=10)
    door_left_open.send_notifications(test_door, duration)
    mt.assert_action_called(Domain.NOTIFY, person.marshall.notify_action_name)
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)


def test_door_closed_cancel_notifs(mt: MaestroTest) -> None:
    # Exterior door jobs are cancelled when door closes
    mt.trigger_state_change(test_door, new=ON)
    mt.trigger_state_change(test_door, new=OFF)
    for time in door_left_open.NOTIFICATION_TIMES:
        job_id = door_left_open.get_job_id(test_door.id, time)
        mt.assert_job_not_scheduled(job_id)

    # Garage door jobs are cancelled when door closes
    mt.trigger_state_change(cover.west_stall, new="open")
    mt.trigger_state_change(cover.west_stall, new="closed")
    for time in door_left_open.NOTIFICATION_TIMES:
        job_id = door_left_open.get_job_id(cover.west_stall.id, time)
        mt.assert_job_not_scheduled(job_id)


def test_silence_notif_action_called(mt: MaestroTest) -> None:
    job_id = door_left_open.get_job_id(test_door.id, door_left_open.NOTIFICATION_TIMES[0])
    action = door_left_open.SILENCE_NOTIF_ACTION_ID
    action_data = {"entity_id": test_door.id}

    # Job is scheduled and then cancelled by silence notif action
    mt.trigger_state_change(test_door, new=ON)
    mt.assert_job_scheduled(job_id, door_left_open.send_notifications)
    mt.trigger_notif_action(action, action_data)
    mt.assert_job_not_scheduled(job_id)
