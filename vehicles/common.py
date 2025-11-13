from maestro.integrations import EntityId
from maestro.registry import (
    binary_sensor,
    button,
    climate,
    cover,
    device_tracker,
    lock,
    maestro,
    number,
    select,
    sensor,
    switch,
    update,
)


class Nyx:
    complication = maestro.nyx_complication

    charging = binary_sensor.nyx_charging
    charger = binary_sensor.nyx_charger
    doors = binary_sensor.nyx_doors
    online = binary_sensor.nyx_online
    windows = binary_sensor.nyx_windows

    flash_lights = button.nyx_flash_lights
    force_data_update = button.nyx_force_data_update
    horn = button.nyx_horn
    remote_start = button.nyx_remote_start
    wake_up = button.nyx_wake_up

    climate = climate.nyx_hvac_climate_system

    charger_door = cover.nyx_charger_door
    frunk = cover.nyx_frunk
    trunk = cover.nyx_trunk
    windows_cover = cover.nyx_windows

    destination = device_tracker.nyx_destination_location_tracker
    location = device_tracker.nyx_location_tracker

    charge_port_latch = lock.nyx_charge_port_latch
    lock = lock.nyx_doors

    charge_limit = number.nyx_charge_limit
    charging_amps = number.nyx_charging_amps

    cabin_overheat_protection = select.nyx_cabin_overheat_protection
    heated_seat_left = select.nyx_heated_seat_left
    heated_seat_rear_center = select.nyx_heated_seat_rear_center
    heated_seat_rear_left = select.nyx_heated_seat_rear_left
    heated_seat_rear_right = select.nyx_heated_seat_rear_right
    heated_seat_right = select.nyx_heated_seat_right
    heated_steering_wheel = select.nyx_heated_steering_wheel

    arrival_time = sensor.nyx_arrival_time
    battery = sensor.nyx_battery
    charger_power = sensor.nyx_charger_power
    charging_rate = sensor.nyx_charging_rate
    data_last_update_time = sensor.nyx_data_last_update_time
    distance_to_arrival = sensor.nyx_distance_to_arrival
    energy_added = sensor.nyx_energy_added
    odometer = sensor.nyx_odometer
    polling_interval = sensor.nyx_polling_interval
    range = sensor.nyx_range
    shift_state = sensor.nyx_shift_state
    temperature_inside = sensor.nyx_temperature_inside
    temperature_outside = sensor.nyx_temperature_outside
    time_charge_complete = sensor.nyx_time_charge_complete
    tpms_front_left = sensor.nyx_tpms_front_left
    tpms_front_right = sensor.nyx_tpms_front_right
    tpms_rear_left = sensor.nyx_tpms_rear_left
    tpms_rear_right = sensor.nyx_tpms_rear_right

    charger_switch = switch.nyx_charger
    heated_steering = switch.nyx_heated_steering
    polling = switch.nyx_polling
    sentry_mode = switch.nyx_sentry_mode
    valet_mode = switch.nyx_valet_mode

    software_update = update.nyx_software_update


class Tess:
    complication = maestro.tess_complication

    charging = binary_sensor.tess_charging
    charger = binary_sensor.tess_charger
    doors = binary_sensor.tess_doors
    online = binary_sensor.tess_online
    windows = binary_sensor.tess_windows

    flash_lights = button.tess_flash_lights
    force_data_update = button.tess_force_data_update
    horn = button.tess_horn
    remote_start = button.tess_remote_start
    wake_up = button.tess_wake_up

    climate = climate.tess_hvac_climate_system

    charger_door = cover.tess_charger_door
    frunk = cover.tess_frunk
    trunk = cover.tess_trunk
    windows_cover = cover.tess_windows

    destination = device_tracker.tess_destination_location_tracker
    location = device_tracker.tess_location_tracker

    charge_port_latch = lock.tess_charge_port_latch
    lock = lock.tess_doors

    charge_limit = number.tess_charge_limit
    charging_amps = number.tess_charging_amps

    cabin_overheat_protection = select.tess_cabin_overheat_protection
    heated_seat_left = select.tess_heated_seat_left
    heated_seat_rear_center = select.tess_heated_seat_rear_center
    heated_seat_rear_left = select.tess_heated_seat_rear_left
    heated_seat_rear_right = select.tess_heated_seat_rear_right
    heated_seat_right = select.tess_heated_seat_right
    heated_steering_wheel = select.tess_heated_steering_wheel

    arrival_time = sensor.tess_arrival_time
    battery = sensor.tess_battery
    charger_power = sensor.tess_charger_power
    charging_rate = sensor.tess_charging_rate
    data_last_update_time = sensor.tess_data_last_update_time
    distance_to_arrival = sensor.tess_distance_to_arrival
    energy_added = sensor.tess_energy_added
    odometer = sensor.tess_odometer
    polling_interval = sensor.tess_polling_interval
    range = sensor.tess_range
    shift_state = sensor.tess_shift_state
    temperature_inside = sensor.tess_temperature_inside
    temperature_outside = sensor.tess_temperature_outside
    time_charge_complete = sensor.tess_time_charge_complete
    tpms_front_left = sensor.tess_tpms_front_left
    tpms_front_right = sensor.tess_tpms_front_right
    tpms_rear_left = sensor.tess_tpms_rear_left
    tpms_rear_right = sensor.tess_tpms_rear_right

    charger_switch = switch.tess_charger
    heated_steering = switch.tess_heated_steering
    polling = switch.tess_polling
    sentry_mode = switch.tess_sentry_mode
    valet_mode = switch.tess_valet_mode

    software_update = update.tess_software_update


def get_vehicle_config(entity_id: EntityId) -> type[Nyx] | type[Tess]:
    return Tess if "tess" in entity_id else Nyx
