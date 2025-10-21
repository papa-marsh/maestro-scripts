from enum import StrEnum, auto

from maestro.domains.climate import Climate


class Thermostat(Climate):
    class HVACMode(StrEnum):
        OFF = auto()
        COOL = auto()
        HEAT = auto()

    class FanMode(StrEnum):
        ON = auto()
        AUTO = auto()
        DIFFUSE = auto()

    class PresetMode(StrEnum):
        NONE = auto()
        AWAY = auto()
        HOLD = auto()

    def set_fan_mode(self, mode: FanMode) -> None:
        self.perform_action("set_fan_mode", mode=mode)

    def set_hvac_mode(self, mode: HVACMode) -> None:
        self.perform_action("set_hvac_mode", mode=mode)

    def set_preset_mode(self, mode: PresetMode) -> None:
        self.perform_action("set_preset_mode", mode=mode)


class BathroomFloor(Climate):
    class HVACMode(StrEnum):
        AUTO = auto()
        HEAT = auto()

    class PresetMode(StrEnum):
        RUN_SCHEDULE = "Run Schedule"
        TEMPORARY_HOLD = "Temporary Hold"
        PERMANENT_HOLD = "Permanent Hold"

    def set_hvac_mode(self, mode: HVACMode) -> None:
        self.perform_action("set_hvac_mode", mode=mode)

    def set_preset_mode(self, mode: PresetMode) -> None:
        self.perform_action("set_preset_mode", mode=mode)


class TeslaHVAC(Climate):
    class HVACMode(StrEnum):
        OFF = auto()
        HEAT_COOL = auto()

    class FanMode(StrEnum):
        OFF = auto()
        BIOWEAPON = auto()

    class PresetMode(StrEnum):
        NORMAL = auto()
        DEFROST = auto()
        KEEP = auto()
        DOG = auto()
        CAMP = auto()

    def set_fan_mode(self, mode: FanMode) -> None:
        self.perform_action("set_fan_mode", mode=mode)

    def set_hvac_mode(self, mode: HVACMode) -> None:
        self.perform_action("set_hvac_mode", mode=mode)

    def set_preset_mode(self, mode: PresetMode) -> None:
        self.perform_action("set_preset_mode", mode=mode)
