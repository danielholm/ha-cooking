"""Koordinator: lyssnar pa kallsensorerna och haller allt beraknat tillstand."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .calc import HoldTracker, RateTracker
from .const import CONF_AMBIENT_ENTITY, CONF_CORE_ENTITY
from .presets import CUSTOM, PRESETS, SOURCE_AMBIENT, SOURCE_CORE

_LOGGER = logging.getLogger(__name__)

# Tickar aven nar sensorerna star stilla, sa halltiden rakknas upp aven for
# kallor som rapporterar sallan.
TICK = timedelta(seconds=30)


@dataclass
class CookingData:
    """Ogonblicksbild som entiteterna laser."""

    core_temp: float | None = None
    ambient_temp: float | None = None
    hold_seconds: float = 0.0
    hold_inside: bool = False
    hold_done: bool = False
    target_reached: bool = False
    prewarn_reached: bool = False
    rate_per_hour: float | None = None
    eta_seconds: float | None = None


class CookingCoordinator(DataUpdateCoordinator[CookingData]):
    """Raknar pa tva temperaturkallor."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initiera."""
        super().__init__(
            hass,
            _LOGGER,
            name=entry.title,
            update_interval=TICK,
        )
        self.entry = entry
        self.core_entity: str = entry.options.get(
            CONF_CORE_ENTITY, entry.data[CONF_CORE_ENTITY]
        )
        self.ambient_entity: str | None = entry.options.get(
            CONF_AMBIENT_ENTITY, entry.data.get(CONF_AMBIENT_ENTITY)
        )

        # Installningar — agda av number- och select-entiteterna.
        self.preset: str = CUSTOM
        self.target_temp: float | None = None
        self.prewarn_offset: float = 5.0
        self.hold_minutes: float = 0.0
        self.hold_source: str = SOURCE_CORE

        self._hold = HoldTracker()
        self._rate = RateTracker()
        self._target_reached = False
        self._prewarn_reached = False
        self._hold_done = False

    # ---- installningar -------------------------------------------------

    @callback
    def set_hold_bounds(self, minimum: float | None, maximum: float | None) -> None:
        """Satt hallspannet."""
        self._hold.minimum = minimum
        self._hold.maximum = maximum

    @property
    def hold_minimum(self) -> float | None:
        """Undre hallgrans."""
        return self._hold.minimum

    @property
    def hold_maximum(self) -> float | None:
        """Ovre hallgrans."""
        return self._hold.maximum

    @callback
    def apply_preset(self, name: str) -> None:
        """Applicera en forinstallning."""
        preset = PRESETS.get(name)
        if preset is None:
            return
        self.preset = name
        if name == CUSTOM:
            return
        self.target_temp = preset.target
        self.prewarn_offset = preset.prewarn
        self.hold_minutes = preset.hold_minutes
        self.hold_source = preset.hold_source
        self.set_hold_bounds(preset.hold_min, preset.hold_max)
        self.reset()

    @callback
    def note_manual_change(self) -> None:
        """En handandrad siffra betyder att forinstallningen inte langre galler."""
        self.preset = CUSTOM

    @callback
    def reset(self) -> None:
        """Nollstall larm och hallklocka."""
        self._hold.reset()
        self._rate.reset()
        self._target_reached = False
        self._prewarn_reached = False
        self._hold_done = False

    @callback
    def restore_hold_seconds(self, seconds: float) -> None:
        """Aterstall ackumulerad halltid efter omstart."""
        self._hold.seconds = seconds

    # ---- livscykel -----------------------------------------------------

    async def async_setup(self) -> None:
        """Borja lyssna pa kallorna."""
        entities = [self.core_entity]
        if self.ambient_entity:
            entities.append(self.ambient_entity)

        self.entry.async_on_unload(
            async_track_state_change_event(self.hass, entities, self._handle_source)
        )

    @callback
    def _handle_source(self, event: Event[EventStateChangedData]) -> None:
        """En kallsensor har uppdaterats."""
        self.async_set_updated_data(self._compute())

    def _read(self, entity_id: str | None) -> float | None:
        """Las ett numeriskt varde, eller None om det inte gar."""
        if entity_id is None:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable", ""):
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

    async def _async_update_data(self) -> CookingData:
        """Periodisk tick."""
        return self._compute()

    def _compute(self) -> CookingData:
        """Rakna om allt."""
        now: datetime = dt_util.utcnow()
        core = self._read(self.core_entity)
        ambient = self._read(self.ambient_entity)

        hold_value = ambient if self.hold_source == SOURCE_AMBIENT else core
        self._hold.tick(now, hold_value)
        self._rate.add(now, core)

        if self.target_temp is not None and core is not None:
            if core >= self.target_temp:
                self._target_reached = True
            if core >= self.target_temp - self.prewarn_offset:
                self._prewarn_reached = True

        if self.hold_minutes > 0 and self._hold.seconds >= self.hold_minutes * 60:
            self._hold_done = True

        return CookingData(
            core_temp=core,
            ambient_temp=ambient,
            hold_seconds=self._hold.seconds,
            hold_inside=self._hold.inside,
            hold_done=self._hold_done,
            target_reached=self._target_reached,
            prewarn_reached=self._prewarn_reached,
            rate_per_hour=self._rate.rate_per_hour(),
            eta_seconds=self._rate.eta_seconds(core, self.target_temp),
        )
