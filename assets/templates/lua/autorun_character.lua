local PM_NAME = "{{DISPLAY_NAME}}"
local PM_MODEL = "models/player/{{MODEL_ID}}/{{MODEL_ID}}.mdl"
local NPC_MODEL = "models/npc/{{MODEL_ID}}/{{MODEL_ID}}_npc.mdl"
local HANDS_AUTO = "models/arms/{{MODEL_ID}}_arms.mdl"
local HANDS_BARE = "models/arms/{{MODEL_ID}}_arms_bare.mdl"
local HANDS_JK = "models/arms/{{MODEL_ID}}_arms_jk.mdl"
local NPC_CATEGORY = "{{CATEGORY}}"

player_manager.AddValidModel(PM_NAME, PM_MODEL)
player_manager.AddValidHands(PM_NAME, HANDS_AUTO, 0, "00000000")
list.Set("PlayerOptionsModel", PM_NAME, PM_MODEL)

local npcWeapons = {
    "weapon_pistol",
    "weapon_smg1",
    "weapon_ar2",
    "weapon_shotgun"
}

list.Set("NPC", "{{MODEL_ID}}_friendly", {
    Name = PM_NAME .. " (Friendly)",
    Class = "npc_citizen",
    Category = NPC_CATEGORY,
    Model = NPC_MODEL,
    KeyValues = {
        citizentype = 3,
        SquadName = "resistance"
    },
    Weapons = npcWeapons
})

list.Set("NPC", "{{MODEL_ID}}_hostile", {
    Name = PM_NAME .. " (Hostile)",
    Class = "npc_citizen",
    Category = NPC_CATEGORY,
    Model = NPC_MODEL,
    KeyValues = {
        citizentype = 3,
        SquadName = "overwatch",
        Hostile = "1"
    },
    Weapons = npcWeapons
})

if CLIENT then
    local mode = CreateClientConVar(
        "{{MODEL_ID}}_hands_mode",
        "0",
        true,
        false,
        "0=automatic, 1=bare, 2=JK sleeves, 3=generic",
        0,
        3
    )

    hook.Add("PreDrawPlayerHands", "{{HOOK_PREFIX}}CustomHands", function(hands, _viewModel, ply)
        if not IsValid(hands) or not IsValid(ply) then return end
        if string.lower(ply:GetModel() or "") ~= PM_MODEL then return end

        local selected = mode:GetInt()
        local target = HANDS_AUTO

        if selected == 0 then
            {{AUTOMATIC_HANDS_SELECTION}}
        elseif selected == 1 then
            target = HANDS_BARE
        elseif selected == 2 then
            target = HANDS_JK
        elseif selected == 3 then
            target = "models/weapons/c_arms_citizen.mdl"
        end

        if string.lower(hands:GetModel() or "") ~= target then
            hands:SetModel(target)
        end
    end)

    local function closeRagdollEyes(ragdoll)
        if not IsValid(ragdoll) or not ragdoll.GetFlexIDByName then return end
        if not ragdoll:IsRagdoll() then return end

        local model = string.lower(ragdoll:GetModel() or "")
        if model ~= PM_MODEL and model ~= NPC_MODEL then return end

        local blink = ragdoll:GetFlexIDByName("blink")
        if not isnumber(blink) or blink < 0 then return end
        ragdoll:SetFlexWeight(blink, 1)
    end

    local function queueClosedEyes(ragdoll)
        if not IsValid(ragdoll) or not ragdoll:IsRagdoll() then return end
        timer.Simple(0, function() closeRagdollEyes(ragdoll) end)
        timer.Simple(0.1, function() closeRagdollEyes(ragdoll) end)
    end

    hook.Add("CreateClientsideRagdoll", "{{HOOK_PREFIX}}CloseDeathEyes", function(_entity, ragdoll)
        queueClosedEyes(ragdoll)
    end)

    hook.Add("NetworkEntityCreated", "{{HOOK_PREFIX}}CloseNetworkedRagdollEyes", function(entity)
        queueClosedEyes(entity)
    end)
end
