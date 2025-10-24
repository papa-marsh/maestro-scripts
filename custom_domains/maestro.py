from typing import TypedDict

from maestro.domains import Maestro
from maestro.utils import local_now


class AppleWatchComplication(Maestro):
    class GaugeText(TypedDict):
        leading: str
        trailing: str
        outer: str
        gauge: float

    class StackText(TypedDict):
        inner: str
        outer: str

    ComplicationAttributesT = GaugeText | StackText

    def update(self, attributes: ComplicationAttributesT) -> None:
        self.state_manager.upsert_hass_entity(
            entity_id=self.id,
            state=local_now().isoformat(),
            attributes=dict(attributes),
        )
