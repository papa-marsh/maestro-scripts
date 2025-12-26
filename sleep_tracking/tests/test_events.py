from datetime import timedelta

from maestro.app import db
from maestro.integrations import Domain
from maestro.registry import person
from maestro.testing import MaestroTest
from maestro.utils import local_now
from scripts.config.secrets import PERSON_TO_USER_ID

from .. import events
from ..models import SleepEvent


def test_olivia_wakeup_event(mt: MaestroTest) -> None:
    # Event is saved and notification sent for wakeup event
    mt.trigger_event("olivia_awake")
    sleep_events = db.session.query(SleepEvent).all()
    assert len(sleep_events) == 1
    assert sleep_events[0].wakeup is True
    mt.assert_action_called(Domain.NOTIFY, person.marshall.notify_action_name)
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)

    # Wakeup event notifies only Emily and exits if already awake
    mt.clear_action_calls()
    mt.trigger_event("olivia_awake")
    sleep_events = db.session.query(SleepEvent).all()
    assert len(sleep_events) == 1
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)
    mt.assert_action_not_called(Domain.NOTIFY, person.marshall.notify_action_name)


def test_olivia_asleep_event(mt: MaestroTest) -> None:
    one_hour_ago = local_now() - timedelta(hours=1)
    with mt.mock_datetime_as(one_hour_ago):
        mt.trigger_event("olivia_awake")

    # Event is saved and notification sent for asleep event
    mt.trigger_event("olivia_asleep")
    sleep_events = db.session.query(SleepEvent).all()
    assert len(sleep_events) == 2
    assert sleep_events[1].wakeup is False
    mt.assert_action_called(Domain.NOTIFY, person.marshall.notify_action_name)
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)

    # Sleep event notifies only Emily and exits if already asleep
    mt.clear_action_calls()
    mt.trigger_event("olivia_asleep")
    sleep_events = db.session.query(SleepEvent).all()
    assert len(sleep_events) == 2
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)
    mt.assert_action_not_called(Domain.NOTIFY, person.marshall.notify_action_name)


def test_asleep_false_alarm_threshold(mt: MaestroTest) -> None:
    # Asleep event notifies, deletes previous, and exits if below false alarm threshold
    within_threshold_datetime = local_now() - events.FALSE_ALARM_THRESHOLD + timedelta(minutes=1)
    with mt.mock_datetime_as(within_threshold_datetime):
        mt.trigger_event("olivia_awake")

    sleep_events = db.session.query(SleepEvent).all()
    assert len(sleep_events) == 1
    mt.clear_action_calls()

    mt.trigger_event("olivia_asleep")
    sleep_events = db.session.query(SleepEvent).all()
    assert len(sleep_events) == 0
    mt.assert_action_called(Domain.NOTIFY, person.marshall.notify_action_name)
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)


def test_wakeup_false_alarm_threshold(mt: MaestroTest) -> None:
    one_hour_ago = local_now() - timedelta(hours=1)
    with mt.mock_datetime_as(one_hour_ago):
        mt.trigger_event("olivia_awake")

    # Wakeup event notifies, deletes previous, and exits if below false alarm threshold
    within_threshold_datetime = local_now() - events.FALSE_ALARM_THRESHOLD + timedelta(minutes=1)
    with mt.mock_datetime_as(within_threshold_datetime):
        mt.trigger_event("olivia_asleep")

    sleep_events = db.session.query(SleepEvent).all()
    assert len(sleep_events) == 2
    mt.clear_action_calls()

    mt.trigger_event("olivia_awake")
    sleep_events = db.session.query(SleepEvent).all()
    assert len(sleep_events) == 1
    mt.assert_action_called(Domain.NOTIFY, person.marshall.notify_action_name)
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)


def test_olivia_info(mt: MaestroTest) -> None:
    # Notification is sent to requestor only
    mt.trigger_event("olivia_awake")
    mt.clear_action_calls()

    mt.trigger_event("olivia_info", user_id=PERSON_TO_USER_ID[person.marshall])
    mt.assert_action_called(Domain.NOTIFY, person.marshall.notify_action_name)
    mt.assert_action_not_called(Domain.NOTIFY, person.emily.notify_action_name)

    mt.clear_action_calls()
    mt.trigger_event("olivia_info", user_id=PERSON_TO_USER_ID[person.emily])
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)
    mt.assert_action_not_called(Domain.NOTIFY, person.marshall.notify_action_name)
