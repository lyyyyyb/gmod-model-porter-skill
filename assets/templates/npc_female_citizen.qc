// Use the same validated meshes, flexes, hitboxes, jigglebones, and physics as the PM.
// Replace every {{TOKEN}}. Do not include f_anm.mdl in this NPC build.
$modelname "npc/{{MODEL_ID}}/{{MODEL_ID}}_npc.mdl"

$model "{{MODEL_ID}}" "{{FACE_MESH}}" {
    NoAutoDMXRules
    flexcontroller "face" range 0 1 "blink"
    "%blink" = "blink"
    {{OTHER_FLEX_RULES}}
}

$bodygroup "body"
{
    studio "{{BODY_MESH}}"
}

{{BODYGROUP_BLOCKS}}

$surfaceprop "flesh"
$contents "solid"
$cdmaterials "models/{{MODEL_ID}}"
$mostlyopaque
$ambientboost
$illumposition {{ILLUM_X}} {{ILLUM_Y}} {{ILLUM_Z}}

{{ATTACHMENT_BLOCKS}}
{{JIGGLEBONE_BLOCKS}}

$hboxset "default"
{{MEASURED_HITBOX_BLOCKS}}

$sequence ragdoll "{{RAGDOLL_ANIMATION}}" ACT_DIERAGDOLL 1
{{PROPORTION_SEQUENCE}}
$includemodel "humans/female_gestures.mdl"
$includemodel "humans/female_postures.mdl"
$includemodel "humans/female_shared.mdl"
$includemodel "humans/female_ss.mdl"

$collisionjoints "{{PHYSICS_MESH}}"
{
    $mass {{MASS}}
    $inertia 10
    $damping 0.01
    $rotdamping 1.5
    $rootbone "ValveBiped.Bip01_Pelvis"
    {{CONSTRAINT_BLOCKS}}
}
