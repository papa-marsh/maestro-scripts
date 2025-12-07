from maestro.domains import InputText
from maestro.domains.entity import EntityAttribute
from maestro.utils import local_now


class GaugeTextComplication(InputText):
    leading = EntityAttribute(str)
    trailing = EntityAttribute(str)
    outer = EntityAttribute(str)
    gauge = EntityAttribute(float)

    def update(
        self,
        leading: str | None = None,
        trailing: str | None = None,
        outer: str | None = None,
        gauge: float | None = None,
    ) -> None:
        now = local_now()
        self.state_manager.upsert_hass_entity(
            entity_id=self.id,
            state=now.isoformat(),
            attributes={
                "leading": leading,
                "trailing": trailing,
                "outer": outer,
                "gauge": gauge,
                "last_changed": now,
                "last_reported": now,
                "last_updated": now,
            },
        )
