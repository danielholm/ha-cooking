"""Konfigurationsflode: valj namn och kallsensorer."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
)

from .const import CONF_AMBIENT_ENTITY, CONF_CORE_ENTITY, DOMAIN

_TEMPERATURE_SELECTOR = EntitySelector(
    EntitySelectorConfig(domain="sensor", device_class=SensorDeviceClass.TEMPERATURE)
)

_SOURCES = vol.Schema(
    {
        vol.Required(CONF_CORE_ENTITY): _TEMPERATURE_SELECTOR,
        vol.Optional(CONF_AMBIENT_ENTITY): _TEMPERATURE_SELECTOR,
    }
)


class CookingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Skapa en tillagning."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Namnge tillagningen och peka ut kallorna."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME], data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_SOURCES.extend(
                {vol.Required(CONF_NAME): TextSelector()}
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        """Kallorna ska ga att byta i efterhand."""
        return CookingOptionsFlow()


class CookingOptionsFlow(OptionsFlow):
    """Byt kallsensorer."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Visa och spara kallorna."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(_SOURCES, current),
        )
