"""Matlagning — malttemperatur, forvarning och halltid ovanpa valfria sensorer."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .coordinator import CookingCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
]

CookingConfigEntry = ConfigEntry


def cooking_device_info(entry: ConfigEntry) -> DeviceInfo:
    """En enhet per tillagning, sa alla entiteter samlas pa ett kort.

    Utan entry_type renderas den som en vanlig enhet i stallet for som en
    tjanst, vilket ger enhetskortet med alla sensorer samlade.
    """
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Cooking",
        model="Tillagning",
    )


async def async_setup_entry(hass: HomeAssistant, entry: CookingConfigEntry) -> bool:
    """Satt upp en tillagning."""
    coordinator = CookingCoordinator(hass, entry)
    await coordinator.async_setup()
    entry.runtime_data = coordinator

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass: HomeAssistant, entry: CookingConfigEntry) -> None:
    """Ladda om nar kallorna andras."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: CookingConfigEntry) -> bool:
    """Ta bort en tillagning."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
