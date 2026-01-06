from dataclasses import dataclass
from enum import StrEnum

from scripts.frontend.common.icons import Icon


class RowColor(StrEnum):
    DEFAULT = "default"
    GREEN = "green"
    RED = "red"


@dataclass
class EntityCardAttributes:
    title: str
    icon: str
    active: bool = False
    blink: bool = False

    row_1_value: str = "Loading..."
    row_1_icon: Icon = Icon.PROGRESS_QUESTION
    row_2_color: RowColor = RowColor.DEFAULT
    row_2_value: str = "Loading..."
    row_2_icon: Icon = Icon.PROGRESS_QUESTION
    row_1_color: RowColor = RowColor.DEFAULT
    row_3_value: str = "Loading..."
    row_3_icon: Icon = Icon.PROGRESS_QUESTION
    row_3_color: RowColor = RowColor.DEFAULT
