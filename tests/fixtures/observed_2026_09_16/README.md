# Observed payloads, 2026-09-16 / 17 (Taiwan cloud, three Hitachi RAD-series ceiling-embedded air conditioners of different capacities; exact models withheld)

Captured with LibJciHitachi 1.7.2 + this branch, `JciHitachiAWSAPI(...).login()` with hooks on
`_on_publish`, `_on_get_named_shadow_accepted` and `httpx.Client.send`. Nothing is hand-written;
only identifiers were replaced:

| placeholder | replaces |
|---|---|
| `<identity>` | the account's Cognito identity id (`ap-northeast-1:<uuid>`) |
| `<gw-A>` `<gw-B>` `<gw-C>` | the three 14-digit gateway ids (thing-name suffix, shadow client token), in `GetAllDevice` order |
| `Device A/B/C` | `CustomDeviceName` |
| `<redacted>` | `GeoLoc` coordinates |
| `<uuid>` | `regionID` in the shadow |
| `<ssid>` | `WiFiSSID` in registration / status payloads |

All three devices: `DeviceType 1` (AC), `FirmwareId 3`, `FirmwareVersion 6.0.032`,
`LatestFirmwareVersion 8.0.006:6`. At capture time Device A and Device B were **switched off**,
Device C was **running** (`Switch: 1` in its status).

| file | topic / call | what it shows |
|---|---|---|
| `get_all_device.json` | HTTP `POST /GetAllDevice` | three things; no model field here |
| `registration_response_gw-A.json`, `registration_response_gw-B.json` | `<identity>/<identity>_<gw>/registration/response` | the normal support-code answer of an idle unit. **Contains a raw `0xFF` byte** inside `"Model": "RAD-\xffR"`: not valid UTF-8 (this is why `_on_publish` decodes with `errors="replace"`), and identical for two different models, so the value is corrupted at the source. `IndoorUnitInfo` / `OutdoorUnitInfo` are `H65535V255` (sentinel values). |
| `registration_response_gw-C_running.bin` | same topic, running unit | the 6-byte answer `fc ff ff 1f 01 01` instead of JSON. Its meaning is unknown. |
| `registration_response_gw-B_nested_mqtt_publish.bin` | same topic, idle unit, seen once (2026-09-17 00:36:12) | 761 bytes (the length of this unit's normal JSON answer) that are a **raw MQTT byte stream**: a complete PUBLISH packet for `.../status/response` (QoS 1, packet id 4709, valid status JSON inside) followed by the first 54 bytes of the next PUBLISH. Identity / gateway id / SSID replaced by same-length placeholders so the framing stays valid. Decoded in `tests/test_contract.py`. |
| `status_response_gw-*.json` | `.../status/response` | normal status of all three; `CleanNotification` is `1` for A and B, `0` for C |
| `status-secondary_response_gw-A.json` | `.../status-secondary/response` | a topic the library never requests (the official app does); same shape as `status/response` |
| `status-secondary_response_gw-C_running.bin` | same topic, running unit | the same 6-byte answer |
| `shadow_info_get_accepted.json` | named shadow `info`, `get/accepted` | the three shadow documents; `CleanNotification` / `CleanFilterNotification` / `AntiMoldNotification` are `True` for all three regardless of the status above, so these shadow flags are **not** the app's pending notification |
| `things_after_login.json` | this branch's `AWSThing.available` / `attention_reason` after `login()` | A and B available, C not |

## What was observed about the 6-byte frame (correlation only, no mechanism claimed)

Over one day, on the same account, with the HA integration polling every 30 s:

| time (local) | event | registration/response |
|---|---|---|
| 16:57 | power state of the units not recorded | frame from all three |
| 22:34 | A running (reported by its user), B and C off | frame from A only; B and C answer JSON |
| 23:52 | C switched on from Home Assistant | C starts answering the frame on every poll |
| 23:52–23:58 | A switched off by its user | A stops answering the frame; JSON from 23:58 |
| 00:02 (capture above) | C running, A and B off (`Switch` in the status documents) | frame from C only |
| 00:35–00:38 | B idle | B's `status/response` event fired without JSON once, then B's `registration/response` was the 761-byte raw MQTT stream (fixture below), then JSON again |
| 01:13 | C **still running** (status `Mode` cool, `Switch` 1; Home Assistant showed 25 °C cooling) | C answered JSON again after answering the frame since 23:52. So "running" is not sufficient for the frame; what changed on the unit is not known. |
| 13:01–13:57 (09-17) | all three **idle** (`Switch` 0, `CleanSwitch` 0, `CleanStatus` 0); A and B had finished a freeze clean at 11:45 and 12:40 | after a Home Assistant restart at 13:01, all three answered the frame on every poll while `status/response` stayed JSON (read-only capture at 13:07). At 13:57, after another restart, A answered JSON, B and C still the frame. So running is not necessary for the frame either. |

The official app showed the freeze-clean prompt for B all evening and for A at 23:58; both answered
JSON at that time, so the prompt is not what triggers the frame. The `status/response` field
`CleanNotification` was `1` exactly for the two units the app flagged (A, B) and `0` for C.
