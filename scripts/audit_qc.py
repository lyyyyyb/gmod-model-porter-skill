#!/usr/bin/env python3
"""Audit structural requirements in a Garry's Mod model QC file."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


NPC_INCLUDES = (
    "humans/female_gestures.mdl",
    "humans/female_postures.mdl",
    "humans/female_shared.mdl",
    "humans/female_ss.mdl",
)


def add(issues: list[dict], severity: str, code: str, message: str) -> None:
    issues.append({"severity": severity, "code": code, "message": message})


def has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE) is not None


def determine_kind(text: str, path: Path) -> str:
    model_match = re.search(r'^\s*\$modelname\s+"([^"]+)"', text, re.I | re.M)
    model = model_match.group(1).lower() if model_match else path.name.lower()
    if "/npc/" in "/" + model or "_npc" in model:
        return "npc"
    if model.startswith("arms/") or "/arms/" in "/" + model or "c_arms" in model:
        return "arms"
    return "player"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qc", required=True)
    parser.add_argument("--kind", choices=("auto", "player", "npc", "arms"), default="auto")
    parser.add_argument("--json")
    args = parser.parse_args()

    path = Path(args.qc).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"QC file not found: {path}")
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    lower = text.lower()
    kind = determine_kind(text, path) if args.kind == "auto" else args.kind
    issues: list[dict] = []

    if "{{" in text or "}}" in text:
        add(issues, "error", "UNRESOLVED_TEMPLATE", "QC still contains {{TOKEN}} placeholders")
    for directive in ("modelname", "cdmaterials", "surfaceprop", "contents"):
        if not has(text, rf"^\s*\${directive}\b"):
            add(issues, "error", f"MISSING_{directive.upper()}", f"Missing ${directive}")
    if not has(text, r"^\s*\$(model|body|bodygroup)\b"):
        add(issues, "error", "MISSING_MESH", "No $model, $body, or $bodygroup directive")

    model_match = re.search(r'^\s*\$modelname\s+"([^"]+)"', text, re.I | re.M)
    model_name = model_match.group(1).replace("\\", "/") if model_match else ""
    has_collision = has(text, r"^\s*\$(collisionmodel|collisionjoints)\b")

    if kind == "player":
        if not model_name.lower().startswith("player/"):
            add(issues, "error", "PLAYER_MODEL_PATH", "Player QC $modelname must start with player/")
        if 'f_anm.mdl' not in lower:
            add(issues, "error", "PLAYER_ANIMATIONS", "Player QC must include f_anm.mdl")
        if not has_collision:
            add(issues, "error", "PLAYER_COLLISION", "Player QC needs $collisionmodel or $collisionjoints")
        if not has(text, r"^\s*\$(hboxset|hitboxset)\b") or not has(text, r"^\s*\$(hbox|hitbox)\b"):
            add(issues, "error", "PLAYER_HITBOX", "Player QC needs a hitbox set and hitboxes")
        if not has(text, r"^\s*\$attachment\b"):
            add(issues, "warning", "PLAYER_ATTACHMENTS", "No attachments found")
        if "blink" not in lower:
            add(issues, "warning", "PLAYER_BLINK", "No blink flex/controller found")
        if not has(text, r"\$sequence\s+\"?ragdoll\b"):
            add(issues, "warning", "PLAYER_RAGDOLL_SEQUENCE", "No ragdoll sequence found")

    elif kind == "npc":
        if not model_name.lower().startswith("npc/"):
            add(issues, "error", "NPC_MODEL_PATH", "NPC QC $modelname must start with npc/")
        for include in NPC_INCLUDES:
            if include not in lower:
                add(issues, "error", "NPC_ANIMATIONS", f"Missing NPC animation include: {include}")
        if "f_anm.mdl" in lower:
            add(issues, "warning", "NPC_PM_ANIMATIONS", "NPC QC still includes f_anm.mdl")
        if not has_collision:
            add(issues, "error", "NPC_COLLISION", "NPC QC needs $collisionmodel or $collisionjoints")
        if not has(text, r"^\s*\$(hbox|hitbox)\b"):
            add(issues, "error", "NPC_HITBOX", "NPC QC needs hitboxes")

    else:
        if not (model_name.lower().startswith("arms/") or model_name.lower().startswith("weapons/")):
            add(issues, "error", "ARMS_MODEL_PATH", "C-Arms $modelname should start with arms/ or weapons/")
        if "weapons/c_arms_animations.mdl" not in lower:
            add(issues, "error", "ARMS_ANIMATIONS", "C-Arms QC must include weapons/c_arms_animations.mdl")
        define_bones = len(re.findall(r"^\s*\$definebone\b", text, re.I | re.M))
        if define_bones and define_bones != 47:
            add(issues, "error", "ARMS_BONE_COUNT", f"Expected 47 $definebone entries, found {define_bones}")
        elif not define_bones:
            add(issues, "warning", "ARMS_BONE_COUNT", "No $definebone entries; verify 47 bones in exported SMD/DMX")
        if not has(text, r"^\s*\$bonemerge\b"):
            add(issues, "warning", "ARMS_BONEMERGE", "No $bonemerge directives found")

    report = {
        "qc": str(path),
        "kind": kind,
        "model_name": model_name,
        "errors": sum(item["severity"] == "error" for item in issues),
        "warnings": sum(item["severity"] == "warning" for item in issues),
        "issues": issues,
    }
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.json:
        out_path = Path(args.json).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output + "\n", encoding="utf-8")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
