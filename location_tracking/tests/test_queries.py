from datetime import timedelta

from maestro.registry import person
from maestro.testing import MaestroTest
from maestro.utils import local_now

from .. import queries

test_person = person.marshall


def test_last_left_home(mt: MaestroTest) -> None:
    # Fetching when there's no stored value returns None
    assert queries.get_last_left_home(test_person) is None

    # Setting a timestamp caches to redis
    now = local_now()
    queries.set_last_left_home(test_person, now)

    # Fetching a stored timestamp returns the correct datetime
    result = queries.get_last_left_home(test_person)
    assert result == now

    # Setting a new timestamp overwrites the old one
    later = now + timedelta(hours=1)
    queries.set_last_left_home(test_person, later)
    result = queries.get_last_left_home(test_person)
    assert result == later

    # Different people have independent values
    emily_time = now + timedelta(hours=2)
    queries.set_last_left_home(person.emily, emily_time)
    assert queries.get_last_left_home(test_person) == later
    assert queries.get_last_left_home(person.emily) == emily_time


def test_last_zone_arrival(mt: MaestroTest) -> None:
    # Fetching when there's no stored value returns None
    assert queries.get_last_zone_arrival(test_person) is None

    # Setting a timestamp caches to redis
    now = local_now()
    queries.set_last_zone_arrival(test_person, now)

    # Fetching a stored timestamp returns the correct datetime
    result = queries.get_last_zone_arrival(test_person)
    assert result == now

    # Setting a new timestamp overwrites the old one
    later = now + timedelta(hours=1)
    queries.set_last_zone_arrival(test_person, later)
    result = queries.get_last_zone_arrival(test_person)
    assert result == later

    # Different people have independent values
    emily_time = now + timedelta(hours=2)
    queries.set_last_zone_arrival(person.emily, emily_time)
    assert queries.get_last_zone_arrival(test_person) == later
    assert queries.get_last_zone_arrival(person.emily) == emily_time
