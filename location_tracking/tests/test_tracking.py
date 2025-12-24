from datetime import UTC, datetime, timedelta

from maestro.app import db
from maestro.registry import person, zone
from maestro.testing import MaestroTest
from maestro.utils import local_now

from .. import tracking
from ..models import ZoneChange

test_person = person.marshall
test_location_name = "Target"
test_region_name = "Grand Rapids"


def test_save_zone_change(mt: MaestroTest) -> None:
    # Zone change is saved to DB when none exist
    mt.trigger_state_change(test_person, new=test_region_name)
    zone_changes = db.session.query(ZoneChange).filter(ZoneChange.person == test_person.id).all()
    assert len(zone_changes) == 1
    assert zone_changes[0].zone_name == test_region_name
    assert zone_changes[0].duration_seconds is None

    # Zone change is saved when previous records exist
    mt.trigger_state_change(test_person, new=test_location_name)
    zone_changes = db.session.query(ZoneChange).filter(ZoneChange.person == test_person.id).all()
    assert len(zone_changes) == 2

    # Previous record's duration is updated by next zone change
    first_zone_change = (
        db.session.query(ZoneChange)
        .filter(ZoneChange.person == test_person.id)
        .order_by(ZoneChange.arrived_at.asc())
        .first()
    )
    assert first_zone_change.duration_seconds is not None


def test_update_zone_duration() -> None:
    # Duration is set correctly on previous zone change
    now = local_now().replace(tzinfo=UTC)
    one_hour_ago = now - timedelta(hours=1)

    previous_zone_change = ZoneChange(
        person=test_person.id,
        arrived_at=one_hour_ago,
        zone_name=test_region_name,
        duration_seconds=None,
    )
    db.session.add(previous_zone_change)
    db.session.commit()
    tracking.update_zone_duration(previous_zone_change, now)

    assert previous_zone_change.duration_seconds is not None
    assert previous_zone_change.duration_seconds == 3600
