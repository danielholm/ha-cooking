"""Halltid, stigningstakt och gissad aterstaende tid."""

from __future__ import annotations

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTime
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
    """Koppla in sensorerna."""
    coordinator: CookingCoordinator = entry.runtime_data
    async_add_entities(
        [
            HoldTimeSensor(coordinator),
            RateSensor(coordinator),
            EtaSensor(coordinator),
        ]
    )


class HoldTimeSensor(CookingEntity, RestoreSensor, SensorEntity):
    """Ackumulerad tid inom hallspannet."""

    _attr_name = "Hålltid uppnådd"
    _attr_icon = "mdi:timer-sand"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: CookingCoordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "hold_time")

    async def async_added_to_hass(self) -> None:
        """En fyra timmar lang jasning ska inte nollstallas av en omstart."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_sensor_data()) is not None:
            if last.native_value is not None:
                self.coordinator.restore_hold_seconds(float(last.native_value))

    @property
    def native_value(self) -> float | None:
        """Sekunder inom spannet."""
        if self.coordinator.data is None:
            return None
        return round(self.coordinator.data.hold_seconds)


class RateSensor(CookingEntity, SensorEntity):
    """Hur snabbt karntemperaturen stiger."""

    _attr_name = "Stigningstakt"
    _attr_icon = "mdi:trending-up"
    _attr_native_unit_of_measurement = "°C/h"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: CookingCoordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "rate")

    @property
    def native_value(self) -> float | None:
        """Grader per timme."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.rate_per_hour


class EtaSensor(CookingEntity, SensorEntity):
    """Grov gissning pa tid kvar till malet."""

    _attr_name = "Beräknad tid kvar"
    _attr_icon = "mdi:clock-outline"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: CookingCoordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "eta")

    @property
    def native_value(self) -> float | None:
        """Sekunder kvar, eller None nar det inte gar att saga."""
        if self.coordinator.data is None:
            return None
        eta = self.coordinator.data.eta_seconds
        return None if eta is None else round(eta)
