#!/usr/bin/env python3
"""Audit a GMod character addon and optionally compare a deployed copy."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


NPC_ANIMATIONS = (
    b"humans/female_gestures.mdl",
    b"humans/female_postures.mdl",
    b"humans/female_shared.mdl",
    b"humans/female_ss.mdl",
)
SOURCE_EXTENSIONS = {".blend", ".fbx", ".qc", ".qci", ".smd", ".dmx", ".vta", ".psd", ".log", ".bak"}
TEXT_EXTENSIONS = {".lua", ".vmt", ".json", ".txt", ".cfg"}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def manifest(root: Path) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.as_posix().lower()):
        relative = path.relative_to(root).as_posix()
        result[relative] = {"bytes": path.stat().st_size, "sha256": file_hash(path)}
    return result


def issue(items: list[dict], severity: str, code: str, path: str, message: str) -> None:
    items.append({"severity": severity, "code": code, "path": path, "message": message})


def normalized_model_path(value: str) -> str:
    return value.replace("\\", "/").lower().lstrip("/")


def audit_model_families(root: Path, issues: list[dict]) -> None:
    for mdl in root.glob("models/**/*.mdl"):
        rel = mdl.relative_to(root).as_posix()
        stem = mdl.with_suffix("")
        path_lower = rel.lower()
        require_phy = path_lower.startswith("models/player/") or path_lower.startswith("models/npc/")
        required = [stem.with_suffix(".vvd"), Path(str(stem) + ".dx90.vtx")]
        if require_phy:
            required.append(stem.with_suffix(".phy"))
        for companion in required:
            if not companion.is_file():
                issue(issues, "error", "MODEL_COMPANION_MISSING", rel, f"Missing {companion.name}")
        dx80 = Path(str(stem) + ".dx80.vtx")
        if require_phy and not dx80.is_file():
            issue(issues, "warning", "MODEL_DX80_MISSING", rel, f"Missing optional compatibility file {dx80.name}")

        if path_lower.startswith("models/npc/"):
            data = mdl.read_bytes().lower()
            for animation in NPC_ANIMATIONS:
                if animation not in data:
                    issue(issues, "error", "NPC_ANIMATION_MISSING", rel, f"Compiled NPC model lacks {animation.decode()}")


def audit_vmt(root: Path, issues: list[dict]) -> None:
    pattern = re.compile(
        r'[\"\']\$(basetexture|bumpmap|detail|envmapmask|phongexponenttexture|selfillummask)[\"\']\s+[\"\']([^\"\']+)[\"\']',
        re.I,
    )
    ignored = ("env_cubemap", "models/shiny", "dev/")
    for vmt in root.glob("materials/**/*.vmt"):
        rel = vmt.relative_to(root).as_posix()
        text = vmt.read_text(encoding="utf-8-sig", errors="replace")
        for key, value in pattern.findall(text):
            texture = value.replace("\\", "/").lower().lstrip("/")
            if texture.startswith(ignored):
                continue
            candidate = root / "materials" / (texture + ".vtf")
            if not candidate.is_file():
                severity = "error" if key.lower() == "basetexture" else "warning"
                issue(issues, severity, "VMT_TEXTURE_MISSING", rel, f"${key} references missing materials/{texture}.vtf")


def audit_lua(root: Path, issues: list[dict], glualint: Path | None) -> dict:
    lua_root = root / "lua"
    lua_files = list(lua_root.rglob("*.lua")) if lua_root.is_dir() else []
    combined = ""
    npc_ids: dict[str, str] = {}
    model_strings: set[str] = set()
    model_pattern = re.compile(r'[\"\'](models[/\\][^\"\']+?\.mdl)[\"\']', re.I)
    npc_id_pattern = re.compile(r'list\.Set\s*\(\s*[\"\']NPC[\"\']\s*,\s*[\"\']([^\"\']+)[\"\']', re.I)

    for lua in lua_files:
        rel = lua.relative_to(root).as_posix()
        text = lua.read_text(encoding="utf-8-sig", errors="replace")
        combined += "\n" + text
        for value in model_pattern.findall(text):
            model_strings.add(normalized_model_path(value))
        for npc_id in npc_id_pattern.findall(text):
            lowered = npc_id.lower()
            if lowered in npc_ids:
                issue(issues, "error", "DUPLICATE_NPC_ID", rel, f"NPC id {npc_id} also appears in {npc_ids[lowered]}")
            else:
                npc_ids[lowered] = rel
        if npc_id_pattern.search(text) and "models/player/" in text.lower() and "models/npc/" not in text.lower():
            issue(issues, "error", "NPC_USES_PLAYER_MODEL", rel, "NPC registration has a player model but no dedicated NPC model")

    for model in sorted(model_strings):
        candidate = root / Path(model)
        if not candidate.is_file() and not model.startswith("models/weapons/"):
            issue(issues, "warning", "LUA_MODEL_NOT_PACKED", "lua", f"Referenced model is not packed locally: {model}")

    player_mdls = list(root.glob("models/player/**/*.mdl"))
    has_blink = any(b"blink" in mdl.read_bytes().lower() for mdl in player_mdls)
    if has_blink and lua_files:
        lower = combined.lower()
        if "getflexidbyname" not in lower or '"blink"' not in lower:
            issue(issues, "warning", "DEATH_BLINK_HANDLER_MISSING", "lua", "Model has blink flex but no Ragdoll death-eye handler was detected")

    lint_result = {"requested": bool(glualint), "exit_code": None, "output": ""}
    if glualint:
        if not glualint.is_file():
            issue(issues, "error", "GLUALINT_MISSING", str(glualint), "GLuaLint executable not found")
        elif lua_root.is_dir():
            completed = subprocess.run(
                [str(glualint), "lint", str(lua_root)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            lint_result.update({"exit_code": completed.returncode, "output": completed.stdout.strip()})
            if completed.returncode:
                issue(issues, "error", "GLUALINT_FAILED", "lua", completed.stdout.strip() or "GLuaLint failed")
    lint_result["lua_file_count"] = len(lua_files)
    return lint_result


def compare_manifests(first: dict[str, dict], second: dict[str, dict]) -> list[dict]:
    differences = []
    for path in sorted(set(first) | set(second), key=str.lower):
        if path not in first:
            differences.append({"path": path, "kind": "only-in-compare"})
        elif path not in second:
            differences.append({"path": path, "kind": "only-in-addon"})
        elif first[path]["sha256"] != second[path]["sha256"]:
            differences.append({"path": path, "kind": "hash"})
    return differences


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--addon", required=True)
    parser.add_argument("--compare")
    parser.add_argument("--glualint")
    parser.add_argument("--json")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failure")
    args = parser.parse_args()

    root = Path(args.addon).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Addon directory not found: {root}")
    issues: list[dict] = []

    if not (root / "addon.json").is_file():
        issue(issues, "warning", "ADDON_JSON_MISSING", "addon.json", "No addon.json found")
    for path in (p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() in SOURCE_EXTENSIONS:
            issue(issues, "warning", "SOURCE_FILE_PACKED", rel, "Development source file is packed in the addon")
        if path.suffix.lower() in TEXT_EXTENSIONS:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            if "{{" in text or "}}" in text:
                issue(issues, "error", "UNRESOLVED_TEMPLATE", rel, "File still contains {{TOKEN}} placeholders")

    audit_model_families(root, issues)
    audit_vmt(root, issues)
    glualint = Path(args.glualint).expanduser().resolve() if args.glualint else None
    lint = audit_lua(root, issues, glualint)
    addon_manifest = manifest(root)

    comparison = None
    if args.compare:
        compare_root = Path(args.compare).expanduser().resolve()
        if not compare_root.is_dir():
            issue(issues, "error", "COMPARE_MISSING", str(compare_root), "Comparison directory not found")
        else:
            other_manifest = manifest(compare_root)
            differences = compare_manifests(addon_manifest, other_manifest)
            comparison = {
                "root": str(compare_root),
                "file_count": len(other_manifest),
                "differences": differences,
            }
            if differences:
                issue(issues, "error", "DEPLOYMENT_MISMATCH", str(compare_root), f"{len(differences)} file/hash differences")

    errors = sum(item["severity"] == "error" for item in issues)
    warnings = sum(item["severity"] == "warning" for item in issues)
    report = {
        "addon": str(root),
        "file_count": len(addon_manifest),
        "bytes": sum(item["bytes"] for item in addon_manifest.values()),
        "errors": errors,
        "warnings": warnings,
        "issues": issues,
        "glualint": lint,
        "comparison": comparison,
        "manifest": addon_manifest,
    }
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.json:
        output_path = Path(args.json).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output + "\n", encoding="utf-8")
    if errors:
        return 1
    if args.strict and warnings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
