"""Installningar som lagras i Home Assistant."""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
    RestoreNumber,
)
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfTime
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
    """Koppla in installningarna."""
    coordinator: CookingCoordinator = entry.runtime_data
    async_add_entities(
        [
            TargetNumber(coordinator),
            PrewarnNumber(coordinator),
            HoldMinNumber(coordinator),
            HoldMaxNumber(coordinator),
            HoldMinutesNumber(coordinator),
        ]
    )


class _CookingNumber(CookingEntity, RestoreNumber, NumberEntity):
    """Gemensamt for de lagrade talen."""

    _attr_mode = NumberMode.BOX
    _attr_native_step = 1

    def __init__(self, coordinator: CookingCoordinator, key: str) -> None:
        """Initiera."""
        super().__init__(coordinator, key)

    async def async_added_to_hass(self) -> None:
        """Aterstall vardet efter omstart."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) is not None:
            self._attr_native_value = last.native_value
        self._push()

    def _push(self) -> None:
        """Skriv vardet till koordinatorn."""
        raise NotImplementedError

    async def async_set_native_value(self, value: float) -> None:
        """Satt nytt varde."""
        self._attr_native_value = value
        self._push()
        # En handandrad siffra betyder att forinstallningen inte langre galler.
        self.coordinator.note_manual_change()
        self.coordinator.reset()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class TargetNumber(_CookingNumber):
    """Maltemperatur for karnan."""

    _attr_name = "Måltemperatur"
    _attr_icon = "mdi:target"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 0
    _attr_native_max_value = 300
    _attr_native_value = 62.0

    def __init__(self, coordinator: CookingCoordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "target")

    def _push(self) -> None:
        self.coordinator.target_temp = self._attr_native_value

    @property
    def native_value(self) -> float | None:
        """Forinstallningen kan ha skrivit ett nytt varde."""
        if self.coordinator.target_temp != self._attr_native_value:
            self._attr_native_value = self.coordinator.target_temp
        return self._attr_native_value


class PrewarnNumber(_CookingNumber):
    """Hur manga grader innan malet forvarningen gar."""

    _attr_name = "Förvarning"
    _attr_icon = "mdi:bell-outline"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 0
    _attr_native_max_value = 50
    _attr_native_value = 5.0
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: CookingCoordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "prewarn")

    def _push(self) -> None:
        self.coordinator.prewarn_offset = self._attr_native_value or 0.0

    @property
    def native_value(self) -> float | None:
        """Speglar koordinatorn."""
        if self.coordinator.prewarn_offset != self._attr_native_value:
            self._attr_native_value = self.coordinator.prewarn_offset
        return self._attr_native_value


class HoldMinNumber(_CookingNumber):
    """Undre grans for hallspannet."""

    _attr_name = "Hålltemp min"
    _attr_icon = "mdi:thermometer-chevron-down"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 0
    _attr_native_max_value = 300
    _attr_native_value = 0.0
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: CookingCoordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "hold_min")

    def _push(self) -> None:
        value = self._attr_native_value
        self.coordinator.set_hold_bounds(
            value if value else None, self.coordinator.hold_maximum
        )

    @property
    def native_value(self) -> float | None:
        """Speglar koordinatorn."""
        current = self.coordinator.hold_minimum or 0.0
        if current != self._attr_native_value:
            self._attr_native_value = current
        return self._attr_native_value


class HoldMaxNumber(_CookingNumber):
    """Ovre grans for hallspannet. 0 betyder inget tak."""

    _attr_name = "Hålltemp max"
    _attr_icon = "mdi:thermometer-chevron-up"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 0
    _attr_native_max_value = 300
    _attr_native_value = 0.0
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: CookingCoordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "hold_max")

    def _push(self) -> None:
        value = self._attr_native_value
        self.coordinator.set_hold_bounds(
            self.coordinator.hold_minimum, value if value else None
        )

    @property
    def native_value(self) -> float | None:
        """Speglar koordinatorn."""
        current = self.coordinator.hold_maximum or 0.0
        if current != self._attr_native_value:
            self._attr_native_value = current
        return self._attr_native_value


class HoldMinutesNumber(_CookingNumber):
    """Hur lange temperaturen ska hallas. 0 stanger av hallarmet."""

    _attr_name = "Hålltid"
    _attr_icon = "mdi:timer-outline"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_native_min_value = 0
    _attr_native_max_value = 1440
    _attr_native_value = 0.0
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: CookingCoordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "hold_minutes")

    def _push(self) -> None:
        self.coordinator.hold_minutes = self._attr_native_value or 0.0

    @property
    def native_value(self) -> float | None:
        """Speglar koordinatorn."""
        if self.coordinator.hold_minutes != self._attr_native_value:
            self._attr_native_value = self.coordinator.hold_minutes
        return self._attr_native_value
