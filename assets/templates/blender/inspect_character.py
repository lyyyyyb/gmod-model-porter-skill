"""Run inside Blender to inventory a character scene without modifying it.

Example:
  blender --background character.blend --python inspect_character.py -- --output report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import bpy
    from mathutils import Vector
except ImportError as exc:
    raise SystemExit("This script must run with Blender's Python") from exc


def rounded(values, digits=6):
    return [round(float(value), digits) for value in values]


def script_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="JSON report path")
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(values)


def mesh_bounds_world(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": rounded(min(point[index] for point in points) for index in range(3)),
        "max": rounded(max(point[index] for point in points) for index in range(3)),
    }


def mesh_record(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    weighted_vertices = set()
    for vertex in mesh.vertices:
        if any(group.weight > 0.0 for group in vertex.groups):
            weighted_vertices.add(vertex.index)
    uv_names = [layer.name for layer in mesh.uv_layers]
    shape_keys = []
    if mesh.shape_keys:
        shape_keys = [key.name for key in mesh.shape_keys.key_blocks]
    armatures = []
    for modifier in obj.modifiers:
        if modifier.type == "ARMATURE":
            armatures.append(modifier.object.name if modifier.object else None)
    warnings = []
    if any(abs(float(value) - 1.0) > 1e-5 for value in obj.scale):
        warnings.append("Object scale is not applied")
    if any(abs(float(value)) > 1e-5 for value in obj.rotation_euler):
        warnings.append("Object rotation is not applied")
    if not uv_names:
        warnings.append("Mesh has no UV map")
    if len(weighted_vertices) < len(mesh.vertices):
        warnings.append(f"{len(mesh.vertices) - len(weighted_vertices)} vertices have no positive vertex-group weights")
    return {
        "name": obj.name,
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "polygons": len(mesh.polygons),
        "triangles": len(mesh.loop_triangles),
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "uv_maps": uv_names,
        "shape_keys": shape_keys,
        "vertex_groups": [group.name for group in obj.vertex_groups],
        "armature_modifiers": armatures,
        "bounds_world": mesh_bounds_world(obj),
        "transform": {
            "location": rounded(obj.location),
            "rotation_euler": rounded(obj.rotation_euler),
            "scale": rounded(obj.scale),
        },
        "warnings": warnings,
    }


def armature_record(obj):
    bones = []
    for bone in obj.data.bones:
        bones.append(
            {
                "name": bone.name,
                "parent": bone.parent.name if bone.parent else None,
                "head_local": rounded(bone.head_local),
                "tail_local": rounded(bone.tail_local),
                "use_deform": bool(bone.use_deform),
            }
        )
    roots = [bone["name"] for bone in bones if bone["parent"] is None]
    return {
        "name": obj.name,
        "bone_count": len(bones),
        "root_bones": roots,
        "bones": bones,
        "transform": {
            "location": rounded(obj.location),
            "rotation_euler": rounded(obj.rotation_euler),
            "scale": rounded(obj.scale),
        },
    }


def combined_bounds(meshes):
    if not meshes:
        return None
    minimum = [float("inf")] * 3
    maximum = [float("-inf")] * 3
    for obj in meshes:
        bounds = mesh_bounds_world(obj)
        for index in range(3):
            minimum[index] = min(minimum[index], bounds["min"][index])
            maximum[index] = max(maximum[index], bounds["max"][index])
    return {"min": rounded(minimum), "max": rounded(maximum), "size": rounded(maximum[i] - minimum[i] for i in range(3))}


def main() -> int:
    args = script_arguments()
    scene = bpy.context.scene
    meshes = sorted((obj for obj in scene.objects if obj.type == "MESH"), key=lambda obj: obj.name.lower())
    armatures = sorted((obj for obj in scene.objects if obj.type == "ARMATURE"), key=lambda obj: obj.name.lower())
    report = {
        "schema_version": 1,
        "blender_version": bpy.app.version_string,
        "blend_file": bpy.data.filepath,
        "scene": scene.name,
        "units": {
            "system": scene.unit_settings.system,
            "scale_length": scene.unit_settings.scale_length,
        },
        "summary": {
            "objects": len(scene.objects),
            "collections": len(bpy.data.collections),
            "meshes": len(meshes),
            "armatures": len(armatures),
            "materials": len(bpy.data.materials),
            "images": len(bpy.data.images),
            "actions": len(bpy.data.actions),
        },
        "character_bounds_world": combined_bounds(meshes),
        "meshes": [mesh_record(obj) for obj in meshes],
        "armatures": [armature_record(obj) for obj in armatures],
        "materials": sorted(material.name for material in bpy.data.materials),
        "actions": sorted(action.name for action in bpy.data.actions),
    }
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + ".tmp")
    temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(output)
    print(json.dumps({"report": str(output), "summary": report["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
