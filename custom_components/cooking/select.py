"""Forinstallningar."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import CookingConfigEntry
from .entity import CookingEntity
from .presets import CUSTOM, PRESET_NAMES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CookingConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Koppla in valjaren."""
    async_add_entities([CookingPresetSelect(entry.runtime_data)])


class CookingPresetSelect(CookingEntity, SelectEntity, RestoreEntity):
    """Valj rekommenderad temperatur for det du lagar."""

    _attr_name = "Förinställning"
    _attr_icon = "mdi:chef-hat"
    _attr_options = PRESET_NAMES

    def __init__(self, coordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "preset")
        self._attr_current_option = CUSTOM

    async def async_added_to_hass(self) -> None:
        """Aterstall valet efter omstart."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            if last.state in PRESET_NAMES:
                self._attr_current_option = last.state
                # Bara markeringen aterstalls. Siffrorna aterstalls av sina
                # egna entiteter, sa forinstallningen far inte skriva over dem.
                self.coordinator.preset = last.state

    async def async_select_option(self, option: str) -> None:
        """Applicera en forinstallning."""
        self._attr_current_option = option
        self.coordinator.apply_preset(option)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    @property
    def current_option(self) -> str | None:
        """Koordinatorn kan ha bytt till Anpassad vid handandring."""
        if self.coordinator.preset != self._attr_current_option:
            self._attr_current_option = self.coordinator.preset
        return self._attr_current_option
