from enum import StrEnum, auto


class EventType(StrEnum):
    BATHROOM_FLOOR = auto()

    MEETING_ACTIVE = auto()

    OLIVIA_ASLEEP = auto()
    OLIVIA_AWAKE = auto()
    OLIVIA_INFO = auto()

    ENTITY_CARD_1_TAP = "entity_card_1_tap"
    ENTITY_CARD_1_DOUBLE_TAP = "entity_card_1_double_tap"
    ENTITY_CARD_1_HOLD = "entity_card_1_hold"
    ENTITY_CARD_2_TAP = "entity_card_2_tap"
    ENTITY_CARD_2_DOUBLE_TAP = "entity_card_2_double_tap"
    ENTITY_CARD_2_HOLD = "entity_card_2_hold"
    ENTITY_CARD_3_TAP = "entity_card_3_tap"
    ENTITY_CARD_3_DOUBLE_TAP = "entity_card_3_double_tap"
    ENTITY_CARD_3_HOLD = "entity_card_3_hold"
    ENTITY_CARD_4_TAP = "entity_card_4_tap"
    ENTITY_CARD_4_DOUBLE_TAP = "entity_card_4_double_tap"
    ENTITY_CARD_4_HOLD = "entity_card_4_hold"
    ENTITY_CARD_5_TAP = "entity_card_5_tap"
    ENTITY_CARD_5_DOUBLE_TAP = "entity_card_5_double_tap"
    ENTITY_CARD_5_HOLD = "entity_card_5_hold"
    ENTITY_CARD_6_TAP = "entity_card_6_tap"
    ENTITY_CARD_6_DOUBLE_TAP = "entity_card_6_double_tap"
    ENTITY_CARD_6_HOLD = "entity_card_6_hold"
