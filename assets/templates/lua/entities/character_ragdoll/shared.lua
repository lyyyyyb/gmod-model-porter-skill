ENT.Type = "anim"
ENT.Base = "base_anim"
ENT.PrintName = "{{DISPLAY_NAME}} Ragdoll"
ENT.Category = "{{CATEGORY}}"
ENT.Spawnable = true
ENT.AdminOnly = false

if SERVER then
    local MODEL = "models/player/{{MODEL_ID}}/{{MODEL_ID}}.mdl"

    function ENT:SpawnFunction(ply, trace)
        if not trace.Hit then return end

        local ragdoll = ents.Create("prop_ragdoll")
        if not IsValid(ragdoll) then return end

        ragdoll:SetModel(MODEL)
        ragdoll:SetPos(trace.HitPos + trace.HitNormal * 4)
        if IsValid(ply) then
            ragdoll:SetAngles(Angle(0, ply:EyeAngles().y + 180, 0))
            ragdoll:SetCreator(ply)
        end
        ragdoll:Spawn()
        ragdoll:Activate()
        ragdoll:DropToFloor()
        return ragdoll
    end
end
