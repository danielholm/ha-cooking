"""Larm."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CookingConfigEntry
from .coordinator import CookingCoordinator
from .entity import CookingEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CookingConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Koppla in larmen."""
    coordinator: CookingCoordinator = entry.runtime_data
    async_add_entities(
        [
            PrewarnBinarySensor(coordinator),
            TargetBinarySensor(coordinator),
            HoldInsideBinarySensor(coordinator),
            HoldDoneBinarySensor(coordinator),
        ]
    )


class _CookingBinarySensor(CookingEntity, BinarySensorEntity):
    """Gemensamt."""

    _attr_device_class = BinarySensorDeviceClass.HEAT


class PrewarnBinarySensor(_CookingBinarySensor):
    """Forvarning — latchad."""

    _attr_name = "Snart klar"
    _attr_icon = "mdi:bell-outline"

    def __init__(self, coordinator: CookingCoordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "prewarn_reached")

    @property
    def is_on(self) -> bool | None:
        """Latchat."""
        data = self.coordinator.data
        return None if data is None else data.prewarn_reached


class TargetBinarySensor(_CookingBinarySensor):
    """Maltemperaturen uppnadd — latchad."""

    _attr_name = "Måltemp uppnådd"
    _attr_icon = "mdi:target"

    def __init__(self, coordinator: CookingCoordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "target_reached")

    @property
    def is_on(self) -> bool | None:
        """Latchat."""
        data = self.coordinator.data
        return None if data is None else data.target_reached


class HoldInsideBinarySensor(_CookingBinarySensor):
    """Just nu inom hallspannet — inte latchad."""

    _attr_name = "Inom hållspann"
    _attr_icon = "mdi:thermometer-check"

    def __init__(self, coordinator: CookingCoordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "hold_inside")

    @property
    def is_on(self) -> bool | None:
        """Ogonblicksvarde."""
        data = self.coordinator.data
        return None if data is None else data.hold_inside


class HoldDoneBinarySensor(_CookingBinarySensor):
    """Halltiden fullgjord — latchad."""

    _attr_name = "Hålltid klar"
    _attr_icon = "mdi:timer-check"

    def __init__(self, coordinator: CookingCoordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "hold_done")

    @property
    def is_on(self) -> bool | None:
        """Latchat."""
        data = self.coordinator.data
        return None if data is None else data.hold_done
