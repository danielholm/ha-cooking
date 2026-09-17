"""Gemensam basklass."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import cooking_device_info
from .coordinator import CookingCoordinator


class CookingEntity(CoordinatorEntity[CookingCoordinator]):
    """Entitet knuten till en tillagning."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CookingCoordinator, key: str) -> None:
        """Initiera."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_device_info = cooking_device_info(coordinator.entry)
