#!/usr/bin/env python3
"""Atomically save and resume a GMod model-porting work state."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_state(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"State is not a JSON object: {path}")
    return data


def artifact_record(value: str, root: Path) -> dict:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    record = {"path": str(candidate), "exists": candidate.exists()}
    if candidate.is_file():
        record.update({"type": "file", "bytes": candidate.stat().st_size, "sha256": sha256(candidate)})
    elif candidate.is_dir():
        record.update({"type": "directory", "file_count": sum(1 for p in candidate.rglob("*") if p.is_file())})
    else:
        record["type"] = "missing"
    return record


def write_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--work-root", required=True, help="Model porting work directory")
    result.add_argument("--state-file", default=".gmod-port-state.json")
    result.add_argument("--show", action="store_true")
    result.add_argument("--task")
    result.add_argument("--status")
    result.add_argument("--next", dest="next_action")
    result.add_argument("--note", action="append", default=[])
    result.add_argument("--artifact", action="append", default=[])
    result.add_argument("--attempt", help="Increment the attempt counter for a technical route")
    return result


def main() -> int:
    args = parser().parse_args()
    root = Path(args.work_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    state_path = root / args.state_file
    state = read_state(state_path)

    if args.show:
        if not state:
            print(f"No saved state: {state_path}")
            return 1
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0

    if not args.task and not state.get("task"):
        raise SystemExit("--task is required for the first checkpoint")
    if not args.status and not state.get("status"):
        raise SystemExit("--status is required for the first checkpoint")
    if not args.next_action and not state.get("next_action"):
        raise SystemExit("--next is required for the first checkpoint")

    created_at = state.get("created_at", now_iso())
    notes = list(state.get("notes", []))
    for note in args.note:
        if note not in notes:
            notes.append(note)

    artifacts = {item.get("path"): item for item in state.get("artifacts", []) if item.get("path")}
    for value in args.artifact:
        record = artifact_record(value, root)
        artifacts[record["path"]] = record

    attempts = dict(state.get("attempts", {}))
    change_required = list(state.get("change_approach_required", []))
    if args.attempt:
        attempts[args.attempt] = int(attempts.get(args.attempt, 0)) + 1
        if attempts[args.attempt] >= 3 and args.attempt not in change_required:
            change_required.append(args.attempt)

    state = {
        "task": args.task or state.get("task"),
        "created_at": created_at,
        "updated_at": now_iso(),
        "work_root": str(root),
        "status": args.status or state.get("status"),
        "next_action": args.next_action or state.get("next_action"),
        "notes": notes,
        "artifacts": sorted(artifacts.values(), key=lambda item: item["path"].lower()),
        "attempts": attempts,
        "change_approach_required": change_required,
    }
    write_atomic(state_path, state)
    print(f"Saved: {state_path}")
    print(f"Status: {state['status']}")
    print(f"Next: {state['next_action']}")
    if change_required:
        print("CHANGE_APPROACH_REQUIRED=" + ",".join(change_required))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
