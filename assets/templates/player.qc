// Replace every {{TOKEN}} before compiling. Calculate hitboxes from this model.
$modelname "player/{{MODEL_ID}}/{{MODEL_ID}}.mdl"

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

$attachment "eyes" "ValveBiped.Bip01_Head1" {{EYES_ATTACHMENT}}
$attachment "mouth" "ValveBiped.Bip01_Head1" {{MOUTH_ATTACHMENT}}
$attachment "anim_attachment_RH" "ValveBiped.Bip01_R_Hand" 0 0 0 rotate -90 -90 0
$attachment "anim_attachment_LH" "ValveBiped.Bip01_L_Hand" 0 0 0 rotate -90 -90 0

{{JIGGLEBONE_BLOCKS}}

$hboxset "default"
{{MEASURED_HITBOX_BLOCKS}}

$sequence ragdoll "{{RAGDOLL_ANIMATION}}" ACT_DIERAGDOLL 1
{{PROPORTION_SEQUENCE}}
$includemodel "f_anm.mdl"

$collisionjoints "{{PHYSICS_MESH}}"
{
    $mass {{MASS}}
    $inertia 10
    $damping 0.01
    $rotdamping 1.5
    $rootbone "ValveBiped.Bip01_Pelvis"
    {{CONSTRAINT_BLOCKS}}
}
