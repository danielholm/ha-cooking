"""Ren berakningslogik. Importerar inget fran Home Assistant.

Ligger separat for att kunna testas fristaende — och for att kunna brytas ut
till ett eget paket om integrationen nagon gang ska in i core.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Temperaturen vaggar alltid nagot, och en ugnslucka som oppnas ger en dipp
# pa nagra grader. Utan hysteres skulle hallklockan starta och stanna hela
# tiden. Tvagraderns marginal racker for bade ugn och jasning.
HYSTERESIS_C = 2.0

# Ett langre hopp an sa har betyder att sensorn varit borta, inte att tiden
# verkligen forflutit inom spannet. Rakna inte luckan som halltid.
MAX_TICK = timedelta(minutes=5)

RATE_WINDOW = timedelta(minutes=10)
MIN_RATE_C_PER_HOUR = 0.5


@dataclass
class HoldTracker:
    """Rakna ackumulerad tid inom ett temperaturspann.

    Ackumulerad, inte sammanhangande: oppnar du ugnsluckan pausas klockan och
    fortsatter sedan. For pastorisering ar ackumulerat det enda korrekta, och
    for bakning ar det nastan alltid det man vill ha.
    """

    minimum: float | None = None
    maximum: float | None = None
    seconds: float = 0.0
    inside: bool = False
    _last: datetime | None = field(default=None, repr=False)

    def _within(self, value: float) -> bool:
        """Hysteresen ar asymmetrisk: tuffare att komma in an att falla ur."""
        low = self.minimum
        high = self.maximum
        if self.inside:
            # Redan inne — tillat ett par graders dipp innan klockan pausas.
            if low is not None and value < low - HYSTERESIS_C:
                return False
            if high is not None and value > high + HYSTERESIS_C:
                return False
            return True
        if low is not None and value < low:
            return False
        if high is not None and value > high:
            return False
        return True

    def tick(self, now: datetime, value: float | None) -> None:
        """Mata in ett nytt matvarde."""
        if value is None:
            self.inside = False
            self._last = None
            return

        inside = self._within(value)
        if inside and self.inside and self._last is not None:
            delta = now - self._last
            if timedelta(0) < delta <= MAX_TICK:
                self.seconds += delta.total_seconds()

        self.inside = inside
        self._last = now if inside else None

    def reset(self) -> None:
        """Nollstall klockan."""
        self.seconds = 0.0
        self.inside = False
        self._last = None


@dataclass
class RateTracker:
    """Stigningstakt och grov gissning pa aterstaende tid."""

    window: timedelta = RATE_WINDOW
    samples: deque = field(default_factory=deque)

    def add(self, now: datetime, value: float | None) -> None:
        """Lagg till ett matvarde och slang ut det som fallit ur fonstret."""
        if value is None:
            return
        self.samples.append((now, value))
        cutoff = now - self.window
        while self.samples and self.samples[0][0] < cutoff:
            self.samples.popleft()

    def rate_per_hour(self) -> float | None:
        """Grader per timme, minsta kvadrat over fonstret."""
        if len(self.samples) < 3:
            return None
        t0 = self.samples[0][0]
        xs = [(t - t0).total_seconds() for t, _ in self.samples]
        ys = [v for _, v in self.samples]
        span = xs[-1] - xs[0]
        if span < 60:
            return None

        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        denominator = sum((x - mean_x) ** 2 for x in xs)
        if denominator == 0:
            return None
        slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denominator
        return slope * 3600.0

    def eta_seconds(self, current: float | None, target: float | None) -> float | None:
        """Gissa tid till malet.

        Rak linjar extrapolation. Den ljuger under stall-fasen pa en brisket,
        dar avdunstningen haller temperaturen stilla i timmar, och den ljuger
        nar man narmar sig ugnens temperatur. Behandla som en fingervisning.
        """
        if current is None or target is None or current >= target:
            return None
        rate = self.rate_per_hour()
        if rate is None or rate < MIN_RATE_C_PER_HOUR:
            return None
        return (target - current) / rate * 3600.0

    def reset(self) -> None:
        """Toma fonstret."""
        self.samples.clear()
