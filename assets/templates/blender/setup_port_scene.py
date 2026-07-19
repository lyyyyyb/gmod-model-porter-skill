"""Create an empty, organized Blender workspace for a GMod character port.

Example:
  blender --background --factory-startup --python setup_port_scene.py -- \
    --output C:/ModelPortWork/example/source_work/00_workspace.blend
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import bpy
except ImportError as exc:
    raise SystemExit("This script must run with Blender's Python") from exc


COLLECTIONS = (
    "00_SOURCE_REFERENCE",
    "10_CHARACTER_WORK",
    "20_SKELETON",
    "30_BODYGROUPS",
    "40_C_ARMS",
    "50_PHYSICS",
    "60_EXPORT",
)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New .blend output path")
    parser.add_argument("--target-height", type=float, default=72.0, help="Human height in Source units")
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(values)


def main() -> int:
    args = arguments()
    if args.target_height <= 0:
        raise SystemExit("--target-height must be greater than zero")
    output = Path(args.output).expanduser().resolve()
    if output.suffix.lower() != ".blend":
        raise SystemExit("--output must end in .blend")
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing Blend: {output}")
    if bpy.data.filepath:
        raise SystemExit("Run with --factory-startup; refusing to modify an opened Blend")
    unexpected = [obj.name for obj in bpy.data.objects if obj.name not in {"Cube", "Camera", "Light"}]
    if unexpected:
        raise SystemExit(f"Scene is not a factory startup scene; unexpected objects: {unexpected}")

    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

    scene = bpy.context.scene
    scene["gmod_port_schema_version"] = 1
    scene["gmod_target_human_height_source_units"] = float(args.target_height)
    scene["gmod_original_assets_are_read_only"] = True
    scene["gmod_reference_assets_are_method_only"] = True

    created = []
    for name in COLLECTIONS:
        collection = bpy.data.collections.get(name)
        if collection is None:
            collection = bpy.data.collections.new(name)
            scene.collection.children.link(collection)
            created.append(name)

    source_collection = bpy.data.collections["00_SOURCE_REFERENCE"]
    source_collection.hide_render = True
    source_collection["usage"] = "Keep authorized source/reference objects unchanged; do not export"
    bpy.data.collections["60_EXPORT"]["usage"] = "Only verified export-ready objects"

    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    print(
        json.dumps(
            {
                "workspace_blend": str(output),
                "target_height_source_units": args.target_height,
                "collections": list(COLLECTIONS),
                "created": created,
                "contains_third_party_assets": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
