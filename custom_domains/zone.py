from copy import deepcopy

from maestro.domains import Zone
from maestro.integrations import EntityId, StateManager
from scripts.config.zones import ZoneMetadata, zone_metadata_registry


class ZoneExtended(Zone):
    def __init__(
        self,
        entity_id: str | EntityId,
        state_manager: StateManager | None = None,
    ):
        super().__init__(entity_id=entity_id, state_manager=state_manager)
        self._metadata: ZoneMetadata | None = None

    @property
    def metadata(self) -> ZoneMetadata:
        """Lazy-load metadata to avoid accessing state manager during module import"""
        if self._metadata is None:
            self._metadata = self.get_zone_metadata(self.friendly_name)
        return self._metadata

    @classmethod
    def get_zone_metadata(cls, friendly_name: str) -> ZoneMetadata:
        registry_entry = zone_metadata_registry.get(friendly_name)

        zone_metadata = deepcopy(registry_entry) or ZoneMetadata()

        if zone_metadata.short_name is None:
            zone_metadata.short_name = friendly_name

        return zone_metadata

    @classmethod
    def resolve_zone(cls, friendly_name: str) -> Zone:
        from maestro.registry import zone as zone_registry

        for attr_name in dir(zone_registry):
            attr = getattr(zone_registry, attr_name)
            if isinstance(attr, Zone) and attr.friendly_name == friendly_name:
                return attr

        raise ValueError(f"No zone entity found for friendly_name: {friendly_name}")
