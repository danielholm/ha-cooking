# Cooking

A Home Assistant helper integration that adds target temperature, pre-warning
and hold-time tracking on top of **any temperature sensors**.

It owns no hardware. You point it at a core temperature sensor and optionally
an ambient one, and get the alarms and timing that are missing. Works equally
well with a BLE probe, an oven sensor, a Zigbee thermometer in a proofing
basket, or a Shelly with a temperature input.

Create one instance per thing you are cooking. Two probes means two instances.

[Svenska](README.sv.md)

## Installation

Add this repository as a custom repository in HACS, or copy
`custom_components/cooking/` into your `config/custom_components/`. Restart
Home Assistant.

Then **Settings → Devices & services → Helpers → Create helper → Cooking**.

## Entities

| Entity | Type | Description |
|---|---|---|
| Preset | select | Recommended temperatures, see below |
| Target temperature | number | Target for the core |
| Pre-warning | number | Degrees before the target |
| Hold temp min | number | Lower bound of the hold range |
| Hold temp max | number | Upper bound, 0 = no ceiling |
| Hold time | number | Minutes, 0 = off |
| Almost done | binary_sensor | Latched pre-warning |
| Target reached | binary_sensor | Latched alarm |
| Within hold range | binary_sensor | Instantaneous |
| Hold time complete | binary_sensor | Latched alarm |
| Hold time accumulated | sensor | Seconds |
| Rate of rise | sensor | °C/h |
| Estimated time remaining | sensor | Rough guess |
| Reset | button | Clears alarms and the clock |

## Hold time

Time is **accumulated, not continuous**. Open the oven door and the clock
pauses, then picks up where it left off. For pasteurisation, accumulated is the
only correct behaviour, and for baking it is almost always what you want.

Two mechanisms guard against noise:

**Two degrees of hysteresis.** Temperature always wobbles, and without a margin
the clock would start and stop constantly around the threshold. The margin is
asymmetric — it is harder to enter the range than to fall out of it.

**Gaps longer than five minutes are not counted.** If the sensor was missing,
that time is not verified hold time, so it is not assumed.

Hold time survives restarts. A four-hour proof is not reset by a Home Assistant
update.

## Estimated time remaining

Linear extrapolation over the last ten minutes. It is surprisingly useful
during the warming phase and **wrong during the stall** — the phase where
evaporative cooling holds a brisket at 68 °C for hours. The sensor goes
`unknown` when the rate of rise is too low for a serious estimate, rather than
lying.

This is essentially what Meater charges for. Treat it as an indication, not a
promise.

## Presets

Core temperatures follow the Swedish Food Agency's recommendations where such
exist (poultry, ground meat, pork), and common practice where it is a matter of
preferred doneness rather than safety (beef, lamb). Verify for yourself when it
matters — the list is a convenience, not an authority.

A few set a hold range instead of a target:

- **Sourdough – proofing**: 24–26 °C for four hours
- **Sourdough starter – feeding**: 22–25 °C for six hours
- **Oven – 200 °C for 20 min**: measured on the ambient sensor
- **Smoking – 110 °C**: 105–120 °C, no time limit

Changing a number by hand flips the selector to `Custom`. Choosing a preset
resets the alarms, since the old alarm no longer applies.

## Automation

```yaml
alias: Cooking - done
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.black_target_reached
      - binary_sensor.white_target_reached
      - binary_sensor.sourdough_hold_time_complete
    to: "on"
actions:
  - action: notify.mobile_app_phone
    data:
      message: "{{ trigger.to_state.name }}"
mode: queued
max: 3
```

## Tests

```
python3 tests/test_calc.py
```

`calc.py` imports nothing from Home Assistant and can be run standalone.

## Acknowledgements

The architecture follows the helper integrations already in Home Assistant core
— `threshold`, `derivative`, `min_max` and `generic_thermostat` — which
likewise own no hardware and compute on other integrations' sensors. The
config-flow and coordinator patterns are theirs.

It was written alongside
[bfour-ble](https://github.com/danielholm/bfour-ble), but deliberately shares
nothing with it: any temperature sensor will do.

## A note on how this was built

The design and the code were produced in conversation with **Claude
(Anthropic)**, an LLM. The calculation logic in `calc.py` is deliberately free
of Home Assistant imports so it can be tested in isolation, and the tests in
`tests/` cover the cases that actually bite: an oven door opening mid-bake, a
sensor dropping out, and the stall where no honest estimate is possible.

Verify the preset temperatures against a source you trust before relying on
them for food safety.

## License

MIT
