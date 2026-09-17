"""Enforce contract/profiles/*: every observed fixture must match its schema, and STATUS_DICT must be
able to map every observed enum value. See contract/README.md for the rules.

The validator is deliberately tiny (type / required / properties / additionalProperties) so the test
suite needs no extra dependency; the schema files are still valid JSON Schema draft-07.
"""

import json
from pathlib import Path

import pytest

from JciHitachi.model import STATUS_DICT

ROOT = Path(__file__).resolve().parent.parent
PROFILES = sorted(p for p in (ROOT / "contract" / "profiles").iterdir() if p.is_dir())
FIXTURES = ROOT / "tests" / "fixtures"

_JSON_TYPES = {
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "null": lambda v: v is None,
}


def validate(instance: dict, schema: dict, where: str) -> list[str]:
    """Return a list of violations (empty when the instance satisfies the schema)."""
    problems = []
    if not isinstance(instance, dict):
        return [f"{where}: not an object"]
    props = schema.get("properties", {})
    for key in schema.get("required", []):
        if key not in instance:
            problems.append(f"{where}: required field {key!r} missing")
    if schema.get("additionalProperties") is False:
        for key in instance:
            if key not in props:
                problems.append(
                    f"{where}: field {key!r} is not in the contract (new field from the cloud?)"
                )
    for key, prop in props.items():
        if key not in instance:
            continue
        types = prop["type"] if isinstance(prop["type"], list) else [prop["type"]]
        if not any(_JSON_TYPES[t](instance[key]) for t in types):
            problems.append(
                f"{where}: {key!r} is {type(instance[key]).__name__}, contract says {types}"
            )
    return problems


def _fixture_dir(profile: dict) -> Path:
    return ROOT / profile["fixtures"]


def _load_json_fixture(path: Path):
    # some payloads carry a raw 0xFF byte (Model); decode like the library does
    return json.loads(path.read_bytes().decode(errors="replace"))


def _samples_for(schema: dict, fixture_dir: Path):
    """Yield (name, object) for every source fixture of a schema."""
    for name in schema["x-sources"]:
        data = _load_json_fixture(fixture_dir / name)
        if name.startswith("get_all_device"):
            for i, thing in enumerate(data["results"]["Things"]):
                yield f"{name}#Things[{i}]", thing
        elif name.startswith("shadow_info"):
            for i, doc in enumerate(data):
                yield f"{name}#[{i}].reported", doc["reported"]
        else:
            yield name, data


@pytest.mark.parametrize("profile_dir", PROFILES, ids=lambda p: p.name)
class TestProfile:
    def test_profile_points_at_existing_fixtures_and_schemas(self, profile_dir):
        profile = json.loads((profile_dir / "profile.json").read_text(encoding="utf-8"))
        assert _fixture_dir(profile).is_dir()
        for message, target in profile["messages"].items():
            schema_name = target.split(" ")[0]
            if schema_name.endswith(".schema.json"):
                assert (profile_dir / schema_name).is_file(), (
                    f"{message} -> {schema_name}"
                )

    def test_every_fixture_matches_its_schema(self, profile_dir):
        profile = json.loads((profile_dir / "profile.json").read_text(encoding="utf-8"))
        fixture_dir = _fixture_dir(profile)
        problems = []
        for schema_path in sorted(profile_dir.glob("*.schema.json")):
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            assert schema.get("additionalProperties") is False, schema_path.name
            count = 0
            for where, obj in _samples_for(schema, fixture_dir):
                count += 1
                problems += validate(obj, schema, f"{schema_path.name} <- {where}")
            assert count == schema["x-samples"], (
                f"{schema_path.name}: x-samples out of date"
            )
        assert not problems, "\n".join(problems)

    def test_observed_enum_values_are_known_to_status_dict(self, profile_dir):
        profile = json.loads((profile_dir / "profile.json").read_text(encoding="utf-8"))
        device_type = (
            STATUS_DICT and {"1": "AC", "2": "DH", "3": "HE"}[profile["DeviceType"]]
        )
        table = STATUS_DICT[device_type]
        fixture_dir = _fixture_dir(profile)
        unknown = []
        for schema_name in ("status_response.schema.json",):
            schema = json.loads((profile_dir / schema_name).read_text(encoding="utf-8"))
            for where, obj in _samples_for(schema, fixture_dir):
                for key, value in obj.items():
                    spec = table.get(key)
                    if spec and not spec["is_numeric"] and value not in spec["id2str"]:
                        unknown.append(
                            f"{where}: {key}={value!r} not in STATUS_DICT[{device_type}][{key}]['id2str']"
                        )
        assert not unknown, "\n".join(unknown)

    def test_x_library_annotations_match_status_dict(self, profile_dir):
        """The schema's view of the library must not drift from STATUS_DICT."""
        profile = json.loads((profile_dir / "profile.json").read_text(encoding="utf-8"))
        table = STATUS_DICT[{"1": "AC", "2": "DH", "3": "HE"}[profile["DeviceType"]]]
        for schema_name in (
            "status_response.schema.json",
            "registration_response.schema.json",
        ):
            schema = json.loads((profile_dir / schema_name).read_text(encoding="utf-8"))
            for key, prop in schema["properties"].items():
                lib = prop.get("x-library")
                if key in table:
                    assert isinstance(lib, dict), (
                        f"{schema_name}: {key} is in STATUS_DICT but schema says {lib!r}"
                    )
                    assert lib["controllable"] == table[key]["controllable"], key
                    assert lib["kind"] == (
                        "numeric" if table[key]["is_numeric"] else "enum"
                    ), key
                else:
                    assert lib == "not in STATUS_DICT", f"{schema_name}: {key}"

    def test_recorded_non_json_answers(self, profile_dir):
        profile = json.loads((profile_dir / "profile.json").read_text(encoding="utf-8"))
        fixture_dir = _fixture_dir(profile)
        frame = profile["non_json_answers"]["bytes_hex"]
        for path in fixture_dir.glob("*_running.bin"):
            assert path.read_bytes().hex() == frame, path.name

        nested = profile.get("nested_mqtt_publish_answer")
        if nested:
            raw = (fixture_dir / nested["fixture"]).read_bytes()
            assert len(raw) == 761
            assert raw[0] == 0x32  # MQTT PUBLISH, QoS 1
            # remaining length varint
            i, mult, remaining = 1, 1, 0
            while True:
                byte = raw[i]
                remaining += (byte & 0x7F) * mult
                mult *= 128
                i += 1
                if not byte & 0x80:
                    break
            assert remaining == 704 and i == 3
            topic_len = int.from_bytes(raw[i : i + 2], "big")
            topic = raw[i + 2 : i + 2 + topic_len].decode()
            assert topic_len == 134 and topic.endswith("/status/response")
            i += 2 + topic_len
            packet_id = int.from_bytes(raw[i : i + 2], "big")
            assert packet_id == 4709
            inner = json.loads(raw[i + 2 : 3 + remaining].decode(errors="replace"))
            assert inner["DeviceType"] == 1 and inner["Switch"] == 0
            tail = raw[3 + remaining :]
            assert len(tail) == 54 and tail[0] == 0x32

    def test_recorded_freeze_clean_timeline(self, profile_dir):
        """An echoed CleanSwitch with Error 0 is not proof that the unit started (2026-09-17)."""
        profile = json.loads((profile_dir / "profile.json").read_text(encoding="utf-8"))
        if "fixtures_freeze_clean" not in profile:
            pytest.skip("profile has no freeze-clean capture")
        rows = [
            json.loads(line)
            for line in (
                ROOT / profile["fixtures_freeze_clean"] / "freeze_clean_timeline.jsonl"
            )
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]

        controls = [r for r in rows if r["event"] == "control"]
        for c in controls:
            assert c["response"]["CleanSwitch"] == c["value"], c["clock"]
            assert c["response"]["Error"] == 0, c["clock"]

        started, not_started = [], []
        for c in (c for c in controls if c["value"] == 1):
            later = [
                r
                for r in rows
                if r["run"] == c["run"]
                and r["clock"] >= c["clock"]
                and r.get("unit") == c["unit"]
                and r["event"] in ("status_response", "control")
                and r is not c
            ]
            window = []
            for r in later:
                if r["event"] == "control":
                    break  # next command to the same unit
                window.append(r["json"])
            (
                started if any(s["CleanStatus"] != 0 for s in window) else not_started
            ).append(c["clock"])
        assert (len(started), len(not_started)) == (3, 4), (started, not_started)
