"""Aterstallning."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CookingConfigEntry
from .entity import CookingEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CookingConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Koppla in knappen."""
    async_add_entities([CookingResetButton(entry.runtime_data)])


class CookingResetButton(CookingEntity, ButtonEntity):
    """Nollstall larm och hallklocka infor nasta tillagning."""

    _attr_name = "Återställ"
    _attr_icon = "mdi:restart"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        """Initiera."""
        super().__init__(coordinator, "reset")

    async def async_press(self) -> None:
        """Nollstall."""
        self.coordinator.reset()
        await self.coordinator.async_request_refresh()
