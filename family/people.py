from maestro.integrations import EntityId
from maestro.registry import binary_sensor, person, sensor
from scripts.vehicles.common import Nyx, Tess


class Marshall:
    person = person.marshall
    vehicle = Nyx

    location = sensor.marshall_s_iphone_geocoded_location

    phone_battery_level = sensor.marshall_s_iphone_battery_level
    phone_battery_state = sensor.marshall_s_iphone_battery_state
    phone_focus = binary_sensor.marshall_s_iphone_focus
    phone_connection = sensor.marshall_s_iphone_connection_type

    app_version = sensor.marshalls_iphone_app_version

    watch_battery_level = sensor.marshalls_iphone_watch_battery
    watch_battery_state = sensor.marshalls_iphone_watch_battery_state


class Emily:
    person = person.emily
    vehicle = Tess

    location = sensor.emily_s_iphone_geocoded_location

    phone_battery_level = sensor.emily_s_iphone_battery_level
    phone_battery_state = sensor.emily_s_iphone_battery_state
    phone_focus = binary_sensor.emily_s_iphone_focus
    phone_connection = sensor.emily_s_iphone_connection_type

    app_version = sensor.emily_s_iphone_app_version

    watch_battery_level = sensor.emily_s_iphone_watch_battery
    watch_battery_state = sensor.emily_s_iphone_watch_battery_state


def get_person_config(entity_id: EntityId) -> type[Marshall] | type[Emily]:
    return Emily if "emily" in entity_id else Marshall
