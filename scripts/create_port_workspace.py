#!/usr/bin/env python3
"""Create a resumable, asset-free workspace for a GMod character port."""

from __future__ import annotations

import argparse
import json
import os
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


DIRECTORIES = (
    "source_original",
    "source_work",
    "unity_extract",
    "compile",
    "compiler_game",
    "addon_stage",
    "release",
    "reports",
    "previews",
    "backups",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_json_atomic(path: Path, data: dict) -> None:
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def load_config_template() -> dict:
    template = Path(__file__).resolve().parent.parent / "assets" / "templates" / "port-config.example.json"
    with template.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config template is not an object: {template}")
    return data


def load_json_template(relative: str) -> dict:
    template = Path(__file__).resolve().parent.parent / "assets" / "templates" / relative
    with template.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON template is not an object: {template}")
    return data


def copy_text_template(relative: str, destination: Path) -> None:
    source = Path(__file__).resolve().parent.parent / "assets" / "templates" / relative
    temp = destination.with_name(destination.name + ".tmp")
    temp.write_text(source.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    os.replace(temp, destination)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--work-root", required=True, help="New or existing work directory")
    result.add_argument("--model-id", required=True, help="Lowercase addon identifier, e.g. example_character")
    result.add_argument("--display-name", help="Display name; defaults to model ID")
    result.add_argument("--target-height", type=float, default=72.0, help="Human body height in Source units")
    return result


def main() -> int:
    args = parser().parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.model_id):
        raise SystemExit("--model-id must match [a-z][a-z0-9_]*")
    if args.target_height <= 0:
        raise SystemExit("--target-height must be greater than zero")

    root = Path(args.work_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    for relative in DIRECTORIES:
        (root / relative).mkdir(exist_ok=True)

    config_path = root / "port-config.json"
    if not config_path.exists():
        config = deepcopy(load_config_template())
        config["model"]["id"] = args.model_id
        config["model"]["display_name"] = args.display_name or args.model_id
        config["target"]["human_height_source_units"] = args.target_height
        write_json_atomic(config_path, config)

    source_manifest_path = root / "source_original" / "source-manifest.json"
    if not source_manifest_path.exists():
        source_manifest = deepcopy(load_json_template("source-manifest.example.json"))
        source_manifest["model_id"] = args.model_id
        write_json_atomic(source_manifest_path, source_manifest)

    workshop_description_path = root / "release" / "workshop_description_zh_en.txt"
    if not workshop_description_path.exists():
        copy_text_template("workshop_description_zh_en.txt", workshop_description_path)

    state_path = root / ".gmod-port-state.json"
    if not state_path.exists():
        state = {
            "schema_version": 1,
            "task": f"Port {args.display_name or args.model_id}",
            "status": "workspace-created",
            "next_action": "Record source license and copy authorized inputs into source_original",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "original_assets_copied": False,
            "attempts": {},
            "artifacts": [],
            "notes": ["Generated files contain no character assets."],
        }
        write_json_atomic(state_path, state)

    result = {
        "workspace": str(root),
        "directories": list(DIRECTORIES),
        "config": str(config_path),
        "state": str(state_path),
        "source_manifest": str(source_manifest_path),
        "workshop_description": str(workshop_description_path),
        "existing_files_preserved": True,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
