# Cloud protocol contract (observed)

This directory records what the Hitachi Taiwan cloud (雲端智慧控, AWS IoT) actually sends and accepts,
**as captured from real devices**, so that the library can be developed and reviewed against a written
contract instead of against memory. Every statement here is backed by a fixture under `tests/fixtures/`
and is enforced by `tests/test_contract.py`.

Rules for this directory:

1. **Observed only.** A field, value or message goes in only when a captured payload shows it. Guesses about
   meaning do not go in; use `x-note` to state the fact and, if needed, "meaning unknown".
2. **One profile per device family × firmware.** Different device types (AC / DH / HE / PM2.5 panel) and
   different module firmware versions may well speak different dialects. A profile never claims to cover
   another; `tests/test_contract.py` validates each profile only against its own fixtures.
3. **Provenance on every file.** `profile.json` says what was captured, when, with which library version and
   which official-app version; every schema lists its source fixture files and sample count.
4. **Identifiers are placeholders.** Account identity, gateway ids, device names, coordinates, Wi-Fi SSIDs are
   replaced before anything is committed (`<identity>`, `<gw-A>`, `Device A`, `<redacted>`, `<ssid>`; inside
   binary fixtures, same-length zero/`x` runs so framing stays intact).

## Layout

```
contract/
  README.md              this file
  transport.md           HTTP endpoints, MQTT topics, subscription, shadow: how messages travel
  profiles/
    <family>-<firmware>/
      profile.json       provenance, message → schema map, things seen but not understood
      *.schema.json      JSON Schema (draft-07) per message, with x-observed-* / x-library / x-note
```

`x-library` on a field says how `JciHitachi.model.STATUS_DICT` currently treats it (`numeric` / `enum` with
`id2str`, `controllable`), or `"not in STATUS_DICT"` when the cloud sends a field the library ignores. That is
the drift detector between the code and the wire.

## Profiles

| profile | devices | captured | fixtures |
|---|---|---|---|
| [`ac-rad-fw6.0.032`](profiles/ac-rad-fw6.0.032/profile.json) | 3 × Hitachi RAD-series ceiling-embedded air conditioners (different capacities), `DeviceType 1`, `FirmwareId 3`, `FirmwareVersion 6.0.032` | 2026-09-16/17 | `tests/fixtures/observed_2026_09_16/`, freeze clean: `tests/fixtures/observed_2026_09_17_freeze_clean/` |

Not covered by any profile yet: dehumidifiers (`DeviceType 2`), heat exchangers (`3`), PM2.5 panels (`4`),
any firmware other than 6.0.032, and `control/response` for any command other than `CleanSwitch`. `STATUS_DICT` has DH and
HE tables, but no captured payload backs them in this repository.

## What the tests enforce

For every profile in `profiles/`:

- each fixture named in a schema's `x-sources` validates against that schema: declared field types, all
  `required` fields present, **no unlisted field** (`additionalProperties: false`). A new field from the cloud
  therefore fails the test until someone adds it to the schema with a source.
- for every field that is also in `STATUS_DICT[<DeviceType>]` as an enum, every observed value is a key of
  its `id2str`; a value the library cannot map fails the test.
- the freeze-clean timeline (`fixtures_freeze_clean`) still shows every start echoed with `Error 0`, and 3 of the 7 starts actually cleaning.
- binary fixtures listed in `profile.json` (`non_json_answers`, `nested_mqtt_publish_answer`) still have the
  recorded bytes / structure.

## How to add what you observe

1. Log in with this library and hook `JciHitachiAWSMqttConnection._on_publish` (and, for shadows,
   `_on_get_named_shadow_accepted`) to save raw payloads **outside** any repository.
2. Replace identifiers (see rule 4). Keep bytes otherwise untouched; keep the raw `0xFF` in `Model` if you have it.
3. Put the files under `tests/fixtures/observed_<date>/` with a README stating device family, count, firmware,
   library version, app version, and a timeline of anything unusual.
4. Create or extend a profile: if your `DeviceType` + `FirmwareVersion` already has one, add your files to the
   schemas' `x-sources` and widen `x-observed-values` / `x-observed-range`; otherwise generate a new profile
   directory. Never edit another profile's observations to fit yours.
5. Run `python -m pytest tests/test_contract.py`. If a fixture fails against a schema, the schema is wrong or
   the cloud changed: record which, do not loosen the schema silently.
