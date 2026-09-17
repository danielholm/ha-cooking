"""Forinstallningar for vanliga tillagningar.

Karntemperaturerna foljer Livsmedelsverkets rekommendationer dar sadana finns
(fagel, malet kott, flask), och etablerad praxis dar det handlar om onskad
tillagningsgrad snarare an sakerhet (not, lamm). Kontrollera sjalv for kanslig
tillagning — det har ar en bekvamlighet, inte en auktoritet.
"""

from __future__ import annotations

from dataclasses import dataclass

SOURCE_CORE = "core"
SOURCE_AMBIENT = "ambient"

CUSTOM = "Anpassad"


@dataclass(frozen=True)
class Preset:
    """En forinstallning. None betyder "lamna orort"."""

    target: float | None = None
    prewarn: float = 5.0
    hold_min: float | None = None
    hold_max: float | None = None
    hold_minutes: float = 0.0
    hold_source: str = SOURCE_CORE


PRESETS: dict[str, Preset] = {
    CUSTOM: Preset(),
    # --- Nöt och lamm: tillagningsgrad, inte säkerhet ---
    "Nöt – blodig": Preset(target=52.0, prewarn=4.0),
    "Nöt – medium rare": Preset(target=55.0, prewarn=4.0),
    "Nöt – medium": Preset(target=60.0, prewarn=4.0),
    "Nöt – genomstekt": Preset(target=70.0, prewarn=5.0),
    "Oxbringa / brisket": Preset(target=94.0, prewarn=8.0),
    "Lamm – rosa": Preset(target=58.0, prewarn=4.0),
    # --- Fläsk ---
    "Fläskkotlett": Preset(target=68.0, prewarn=5.0),
    "Fläskkarré / pulled pork": Preset(target=92.0, prewarn=8.0),
    "Revben": Preset(target=90.0, prewarn=8.0),
    # --- Fågel och fisk ---
    "Kyckling": Preset(target=72.0, prewarn=5.0),
    "Kalkon": Preset(target=72.0, prewarn=5.0),
    "Anka – rosa": Preset(target=58.0, prewarn=4.0),
    "Fisk": Preset(target=52.0, prewarn=3.0),
    # --- Malet kött ---
    "Köttfärslimpa": Preset(target=72.0, prewarn=5.0),
    "Korv": Preset(target=70.0, prewarn=5.0),
    # --- Bak och jäsning ---
    "Surdegsbröd – färdigbakat": Preset(target=97.0, prewarn=4.0),
    "Matbröd – färdigbakat": Preset(target=94.0, prewarn=4.0),
    "Surdeg – jäsning": Preset(
        target=None,
        hold_min=24.0,
        hold_max=26.0,
        hold_minutes=240.0,
        hold_source=SOURCE_CORE,
    ),
    "Surdegsgrund – matning": Preset(
        target=None,
        hold_min=22.0,
        hold_max=25.0,
        hold_minutes=360.0,
        hold_source=SOURCE_CORE,
    ),
    # --- Ugn och grill: mäts på omgivningen ---
    "Ugn – 200 °C i 20 min": Preset(
        target=None,
        hold_min=195.0,
        hold_max=None,
        hold_minutes=20.0,
        hold_source=SOURCE_AMBIENT,
    ),
    "Ugn – 225 °C i 15 min": Preset(
        target=None,
        hold_min=220.0,
        hold_max=None,
        hold_minutes=15.0,
        hold_source=SOURCE_AMBIENT,
    ),
    "Rökning – 110 °C": Preset(
        target=None,
        hold_min=105.0,
        hold_max=120.0,
        hold_minutes=0.0,
        hold_source=SOURCE_AMBIENT,
    ),
}

PRESET_NAMES: list[str] = list(PRESETS)
