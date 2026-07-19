// Keep the standard 47-bone C-Arms skeleton unchanged.
$modelname "arms/{{MODEL_ID}}_arms.mdl"

$bodygroup "arms"
{
    studio "{{ARMS_MESH}}"
}

$surfaceprop "default"
$contents "solid"
$cdmaterials "models/{{MODEL_ID}}"
$ambientboost
$illumposition {{ILLUM_X}} {{ILLUM_Y}} {{ILLUM_Z}}

{{DEFINE_47_BONES}}
{{BONEMERGE_BLOCKS}}
{{PROCEDURAL_BONES}}

$sequence "idle" {
    "{{IDLE_ANIMATION}}"
    fadein 0.2
    fadeout 0.2
    fps 30
}

$includemodel "weapons/c_arms_animations.mdl"
