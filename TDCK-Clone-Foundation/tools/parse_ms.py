#!/usr/bin/env python3
"""Index TDCK .ms scripts without guessing undocumented opcodes.

The first six bytes are preserved as opaque header fields. The payload is
UTF-8 text split by '|'. Only three scene fields are currently interpreted,
where their meaning is supported by repeated, directly inspectable examples:
009 = scene title, 002 = map resource path, 013 = spawn x,y,direction.
All other commands remain raw and are counted, not assigned invented meaning.
"""
from __future__ import annotations
import argparse
import json
import re
from collections import Counter
from pathlib import Path

SCENE_FIELDS = {"009": "title", "002": "mapPath", "013": "spawn"}


def parse_script(path: Path, root: Path, include_commands: bool = False) -> dict:
    raw = path.read_bytes()
    if len(raw) < 6:
        raise ValueError(f"{path}: file shorter than six-byte observed header")
    payload = raw[6:].decode("utf-8")
    tokens = [token for token in payload.split("|") if token]
    commands = []
    for token in tokens:
        opcode = token[:3] if len(token) >= 3 and token[:3].isdigit() else None
        commands.append({"opcode": opcode, "raw": token})

    fields: dict[str, str] = {}
    for command in commands:
        op = command["opcode"]
        if op in SCENE_FIELDS and SCENE_FIELDS[op] not in fields:
            fields[SCENE_FIELDS[op]] = command["raw"][3:]

    scene = None
    map_match = re.fullmatch(r"/?(?:map/)?(\d+)\.map", fields.get("mapPath", ""))
    spawn = None
    if map_match and fields.get("title"):
        values = fields.get("spawn", "").split(",")
        if len(values) >= 2:
            try:
                spawn = {"x": int(values[0]), "y": int(values[1]),
                         "direction": int(values[2]) if len(values) > 2 else None}
            except ValueError:
                spawn = None
        scene = {
            "script": path.relative_to(root).as_posix(),
            "title": fields["title"],
            "mapPath": fields["mapPath"],
            "mapId": map_match.group(1),
            "spawn": spawn,
        }

    counts = Counter(c["opcode"] for c in commands if c["opcode"] is not None)
    record = {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(raw),
        "header": {
            "hex": raw[:6].hex(),
            "u32_be": int.from_bytes(raw[:4], "big", signed=False),
            "u16_be": int.from_bytes(raw[4:6], "big", signed=False),
        },
        "payloadBytes": len(raw) - 6,
        "commandCount": len(commands),
        "opcodeCounts": dict(sorted(counts.items())),
        "scene": scene,
    }
    if include_commands:
        record["commands"] = commands
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Decoded .ms root directory")
    parser.add_argument("--out", type=Path, required=True, help="Output JSON path")
    parser.add_argument("--include-commands", action="store_true", help="Include every raw pipe-delimited command (large output)")
    args = parser.parse_args()
    source = args.source.resolve()
    scripts = sorted(source.rglob("*.ms"), key=lambda p: p.relative_to(source).as_posix())
    records = [parse_script(p, source, include_commands=args.include_commands) for p in scripts]
    scenes = [r["scene"] for r in records if r["scene"] is not None]
    scenes.sort(key=lambda s: (int(s["mapId"]), s["script"]))
    aggregate = Counter()
    for record in records:
        aggregate.update(record["opcodeCounts"])
    output = {
        "format": "TDCK-MS-index-v1",
        "scriptCount": len(records),
        "sceneCount": len(scenes),
        "headerNote": "Six-byte header is retained as opaque data; its semantics are not yet verified.",
        "confirmedSceneFields": SCENE_FIELDS,
        "opcodeCounts": dict(sorted(aggregate.items())),
        "scenes": scenes,
        "scripts": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Indexed {len(records)} scripts; detected {len(scenes)} scene definitions")
    print(f"Output: {args.out.resolve()}")


if __name__ == "__main__":
    main()
