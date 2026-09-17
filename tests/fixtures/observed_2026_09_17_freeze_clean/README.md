# Observed freeze clean (凍結洗淨), 2026-09-17 (profile `ac-rad-fw6.0.032`)

Same account and units as `observed_2026_09_16/`. `Device A` and `Device B` are the same two units as
there (both had `CleanNotification: 1`). The installer's paperwork lists the outdoor unit as a
one-to-many (multi-split) system; `Device C` shares it and was not controlled.

Commands were sent with this branch's `JciHitachiAWSAPI.set_status(status_name="CleanSwitch", ...)`
from a script on the Home Assistant host, while the Home Assistant integration kept polling every
30 s. Because every client of an account receives every `status/response`
(`contract/transport.md` §3.3), the script also recorded the integration's polls, which is why many
status answers are only a few seconds apart.

## Files

| file | what |
|---|---|
| `freeze_clean_timeline.jsonl` | Condensed from the three runs' full logs (about 500 KB, kept on the capture host). Kept rows: every `control` / `control_response` / `decision` / `scenario` / `unit_begin` / `unit_end` / `summary` event. For `status_response`: the first answer per unit per run, every answer where (`Switch`, `CleanSwitch`, `CleanStatus`, `CleanNotification`) changed, the answer just before each change (`"bracket": "last answer before the change"`), and the last answer of each run. `clock` is local time (UTC+8), taken when the answer arrived. In run 1 the `note` texts say `L` for Device B and `S` for Device A. |
| `control_response_clean_start_started.json` | `control/response` to `CleanSwitch: 1`, run 3 11:46:34, after which Device B **did** clean |
| `control_response_clean_start_not_started.json` | `control/response` to `CleanSwitch: 1`, run 2 10:29:20, after which Device B **did not** clean |
| `control_response_clean_stop.json` | `control/response` to `CleanSwitch: 0`, run 1 10:22:44 (interrupting a clean) |

`status_response` rows in the timeline carry every status field except `WiFiSSID`, which the
capture script dropped. So they are not listed as `status_response.schema.json` sources.

## Timeline

A time range "a–b" means that a is the last answer with the old value and b the first with the new one.
"Push" is the official app's iOS notification "<device name>凍結洗淨未執行，請確認是否要重新設定",
with the window in which the account owner received it.

| run | time | action / observation |
|---|---|---|
| 1 | 10:16:20 | Device B: `CleanSwitch: 1` sent; `control/response` echoes `CleanSwitch: 1, Error: 0` |
| 1 | 10:16:20 | Device B status: `CleanSwitch 1, CleanStatus 1` (previous answer 10:16:16 was 0/0) |
| 1 | 10:16:25–10:16:41 | Device B `CleanStatus` 1 → 2 |
| 1 | 10:19:32 | Device A: `CleanSwitch: 1` sent **while Device B is cleaning**; echo `CleanSwitch: 1, Error: 0` |
| 1 | 10:19:32–10:25:39 | Device A status stays `CleanSwitch 0, CleanStatus 0`; push for Device A between 10:19:32 and 10:19:59 |
| 1 | 10:22:44 | Device B: `CleanSwitch: 0` sent; echo `CleanSwitch: 0, Error: 0` |
| 1 | 10:22:41–10:22:46 | Device B status 1/2 → 0/0; `CleanNotification` stays 1 |
| 1 | 10:24:47 | Device B: `CleanSwitch: 1` sent (2 min after the interrupt); echo `CleanSwitch: 1, Error: 0`; status stays 0/0 through 10:25:37; push between 10:24:47 and 10:24:59 |
| 2 | 10:29:20 | Device B: `CleanSwitch: 1` again; echo `Error: 0`; status 0/0 through 10:32:35; push between 10:29:20 and 10:29:49 |
| 2 | 10:39:20 | Device B: `CleanSwitch: 1` again; echo `Error: 0`; status 0/0 through 10:42:50; push between 10:39:20 and 10:39:59 |
| 3 | 10:43:29 | Device A: `CleanSwitch: 1` sent (Device B idle); echo `Error: 0` |
| 3 | 10:43:30 | Device A status `CleanSwitch 1, CleanStatus 1` (previous 10:43:27 was 0/0) |
| 3 | 10:43:50–10:43:54 | Device A `CleanStatus` 1 → 2 |
| 3 | 11:16:03–11:16:33 | Device A `CleanNotification` 1 → 0, still `CleanStatus 2` |
| 3 | 11:45:27–11:45:33 | Device A status 1/2 → 0/0 (about 62 min after the command) |
| 3 | 11:46:34 | Device B: `CleanSwitch: 1` sent (84 min after its interrupt, 1 min after Device A finished); echo `Error: 0` |
| 3 | 11:46:35 | Device B status `CleanSwitch 1, CleanStatus 1` (previous 11:46:32 was 0/0) |
| 3 | 11:46:55–11:47:03 | Device B `CleanStatus` 1 → 2 |
| 3 | 12:11:04–12:11:06 | Device B `CleanNotification` 1 → 0, still `CleanStatus 2` |
| 3 | 12:40:00–12:40:09 | Device B status 1/2 → 0/0 (about 54 min after the command) |

`Switch` stayed 0 on both units the whole time. Between 10:43 and 11:34 the account owner opened the
official app briefly once; nothing in the log changed at that moment.

## What this shows, and what it does not

- **An echo does not mean the unit started.** A `control/response` that echoes `CleanSwitch: 1` with
  `Error: 0` came back for every start: the three that cleaned and the four that did not. The four
  rejected answers have the same key set as the accepted ones. Only the following `status/response`
  (`CleanStatus` leaving 0 within about one second) told them apart.
- **Values seen.** `CleanStatus` went 0 → 1 → 2 on all three accepted starts, and back to 0 at the end
  of both completed cleans and at the interrupt. It stayed 1 for at most 28 s. `CleanNotification` went to 0 part-way through, about 33 min (A) and 25 min (B) after the
  command, not at the end. What 1 and 2 stand for is not stated by the cloud. The library reports
  the raw number. The Home Assistant integration names them from this sequence (idle, starting,
  cleaning) and keeps the raw number as an attribute.
- **Rejected start while another unit cleaned (10:19:32).** This matches the clause for one-to-many
  systems in these indoor units' owner's manual (only one indoor unit can freeze clean at a time). The manual clause
  is recorded in `contract/profiles/ac-rad-fw6.0.032/profile.json`. It is a property of this system,
  not of the cloud API.
- **Rejected restarts after an interrupt (10:24:47, 10:29:20, 10:39:20).** No other unit was cleaning.
  The manual's "not within 60 min after the previous clean" clause speaks of a *completed* clean, and
  Device A started normally at 10:43:29 after its own rejection. The cause of these rejections is
  **unknown**. The last rejection came 17 min after the interrupt, and a start 84 min after it was
  accepted. Nothing in between was tried.
- **Only one data point per unit.** The two clean durations (62 and 54 min) and the two
  notification-clear times are one sample each. They are not a model constant.
