"""Tester for hallklockan och stigningstakten."""

import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PATH = (
    Path(__file__).resolve().parents[1] / "custom_components" / "cooking" / "calc.py"
)
_spec = importlib.util.spec_from_file_location("cooking_calc", _PATH)
_module = importlib.util.module_from_spec(_spec)
sys.modules["cooking_calc"] = _module
_spec.loader.exec_module(_module)

HoldTracker = _module.HoldTracker
RateTracker = _module.RateTracker

T0 = datetime(2026, 9, 16, 18, 0, tzinfo=timezone.utc)


def _minutes(n):
    return T0 + timedelta(minutes=n)


def test_ackumulerar_inom_spannet():
    # 200-gradig ugn, avlast var halvminut i tio minuter.
    hold = HoldTracker(minimum=195.0)
    for i in range(21):
        hold.tick(T0 + timedelta(seconds=30 * i), 205.0)
    assert hold.seconds == 600.0
    assert hold.inside is True


def test_raknar_inte_under_spannet():
    hold = HoldTracker(minimum=195.0)
    hold.tick(_minutes(0), 180.0)
    hold.tick(_minutes(5), 180.0)
    assert hold.seconds == 0.0
    assert hold.inside is False


def test_ugnsluckan_pausar_men_nollstaller_inte():
    hold = HoldTracker(minimum=195.0)
    hold.tick(_minutes(0), 200.0)
    hold.tick(_minutes(5), 200.0)
    assert hold.seconds == 300.0
    # Luckan oppnas, temperaturen rasar.
    hold.tick(_minutes(6), 150.0)
    assert hold.inside is False
    # Tillbaka uppe igen — klockan fortsatter dar den var.
    hold.tick(_minutes(8), 200.0)
    hold.tick(_minutes(10), 200.0)
    assert hold.seconds == 420.0


def test_hysteres_taler_sma_dippar():
    # En grad under grasen ska inte pausa klockan.
    hold = HoldTracker(minimum=195.0)
    hold.tick(_minutes(0), 196.0)
    hold.tick(_minutes(2), 194.0)
    assert hold.inside is True
    assert hold.seconds == 120.0


def test_tak_gor_spann():
    # Jasning: 24-26 grader, avlast varje minut i en halvtimme.
    hold = HoldTracker(minimum=24.0, maximum=26.0)
    for i in range(31):
        hold.tick(_minutes(i), 25.0)
    assert hold.seconds == 1800.0
    # For varmt, med god marginal over hysteresen.
    hold.tick(_minutes(31), 35.0)
    assert hold.inside is False


def test_lang_lucka_raknas_inte():
    # Sensorn var borta i en timme. Den tiden ar inte verifierad halltid.
    hold = HoldTracker(minimum=195.0)
    hold.tick(_minutes(0), 200.0)
    hold.tick(_minutes(60), 200.0)
    assert hold.seconds == 0.0


def test_stigningstakt():
    # 60 grader pa en timme, samplat var minut.
    rate = RateTracker()
    for i in range(11):
        rate.add(_minutes(i), 20.0 + i)
    assert abs(rate.rate_per_hour() - 60.0) < 0.01


def test_eta():
    rate = RateTracker()
    for i in range(11):
        rate.add(_minutes(i), 20.0 + i)
    # 30 grader kvar i 60 grader per timme = en halvtimme.
    eta = rate.eta_seconds(current=30.0, target=60.0)
    assert abs(eta - 1800.0) < 10


def test_eta_tiger_vid_stall():
    # Brisket-stall: temperaturen star still, ingen serios gissning gar att gora.
    rate = RateTracker()
    for i in range(11):
        rate.add(_minutes(i), 68.0)
    assert rate.eta_seconds(current=68.0, target=94.0) is None


def test_eta_tiger_utan_data():
    rate = RateTracker()
    rate.add(_minutes(0), 20.0)
    assert rate.rate_per_hour() is None
    assert rate.eta_seconds(20.0, 60.0) is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\nAlla tester gick igenom.")
