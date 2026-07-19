# GMod Model Porter

一套用于把 Blender、FBX、UnityPackage 或 VRChat 角色完整移植到 Garry's Mod 的 Codex Skill。

它来自 Kaguya 完整转模项目的实际制作、返工和验收经验，不只负责“编译出模型”，还会处理玩家模型、敌友 NPC、Ragdoll、C-Arms、身体组、材质、动骨、Hitbox、眨眼、死亡闭眼、Workshop 打包和游戏目录部署。

> 本仓库只包含通用流程、模板和审查工具，不包含 Kaguya、IKUSIA 或其他作者的原模型、贴图和付费资源。

## 能做什么

- 制作标准 GMod Player Model
- 制作独立 Friendly / Hostile NPC，避免 NPC 使用 PM 动画产生 T 字
- 制作真实 Physics Ragdoll
- 制作自动、裸手、JK 袖等多套标准 47 骨 C-Arms
- 按 Unity 原版还原衣服、配件和尾巴身体组
- 处理 VMT / VTF、双面渲染、透明材质和异常光影
- 从 Unity PhysBone 还原头发、裙摆、耳朵和尾巴 Jigglebone
- 根据人体加权网格制作头顶、手掌和脚部完整 Hitbox
- 支持表情、活体自动眨眼和死亡 Ragdoll 闭眼
- 构建压缩版与原分辨率未压缩版 GMA
- 在部署前后执行 Lua、QC、模型依赖和 SHA256 审查
- 自动保存制作状态，接口或会话中断后继续工作

## 目录

```text
gmod-model-porter-skill/
├── SKILL.md                 Codex 核心执行规则
├── agents/openai.yaml       Skill 显示信息和默认提示词
├── assets/templates/        PM、NPC、C-Arms、Lua、Ragdoll 和 Workshop 模板
├── references/
│   ├── workflow.md          从源文件到 Workshop 的完整制作流程
│   ├── diagnostics.md       T 字、手指、尾巴、材质、动骨等故障诊断
│   ├── kaguya-lessons.md    Kaguya 项目的成功与失败经验
│   ├── review-checklist.md  游戏内外完整验收清单
│   └── toolchain.md         Blender、StudioMDL、GMad 等工具链
└── scripts/
    ├── checkpoint.py        原子保存任务状态和失败次数
    ├── audit_qc.py          审查 PM、NPC、C-Arms QC
    └── audit_addon.py       审查 Addon、材质、NPC 动画、Lua 和部署哈希
```

## 安装

将仓库放到 Codex Skills 目录：

```powershell
git clone https://github.com/lyyyyyb/gmod-model-porter-skill.git `
  "$env:USERPROFILE\.codex\skills\gmod-model-porter"
```

这是私有仓库，克隆时需要登录对应 GitHub 账号。安装后新建一个 Codex 任务，让 Skill 列表重新加载。

## 使用

在新任务中直接输入：

```text
$gmod-model-porter
把 C:\Models\character 中的 Blender 和 UnityPackage 模型制作成完整 GMod Addon，
包含 PM、敌友 NPC、Ragdoll、三套 C-Arms、身体组、眨眼、死亡闭眼、动骨和 Hitbox，
完成后打包 GMA 并替换到我的游戏 addons。
```

也可以直接描述故障：

```text
$gmod-model-porter 检查这个 NPC 为什么是 T 字，并修复后重新部署。
$gmod-model-porter 参考原版 Unity 修复尾巴身体组和颜色重叠。
$gmod-model-porter 对照参考 addon 重做角色自己的 C-Arms，不复制参考网格。
```

## 自动审查

### 保存制作状态

```powershell
python scripts/checkpoint.py `
  --work-root C:\ModelPortWork `
  --task "Port character" `
  --status source-audited `
  --next "Build player model"
```

同一技术路线记录到第三次失败时，脚本会输出 `CHANGE_APPROACH_REQUIRED`，提醒停止继续打补丁并更换方案。

### 审查 QC

```powershell
python scripts/audit_qc.py --qc compile\player.qc --kind player
python scripts/audit_qc.py --qc compile\character_npc.qc --kind npc
python scripts/audit_qc.py --qc compile\arms.qc --kind arms
```

NPC 审查会检查独立 `models/npc/...` 路径和四套女性 Citizen 动画；C-Arms 审查会检查标准动画与 47 骨结构。

### 审查 Addon 和部署结果

```powershell
python scripts/audit_addon.py `
  --addon C:\ModelPortWork\addon_stage `
  --glualint C:\Tools\glualint.exe `
  --json C:\ModelPortWork\reports\addon_audit.json

python scripts/audit_addon.py `
  --addon C:\ModelPortWork\addon_stage `
  --compare F:\SteamLibrary\steamapps\common\GarrysMod\garrysmod\addons\character
```

它会检查模型伴随文件、NPC 动画引用、VMT 贴图、Lua 模型路径、死亡闭眼处理、GLuaLint 和逐文件 SHA256 差异。

## 验收原则

- “StudioMDL 编译成功”不等于完成。
- Blender 固定姿势图不能代替 GMod 真实武器截图。
- 活体自动眨眼和死亡闭眼必须分开验收。
- NPC 必须使用独立 NPC 模型，不能直接使用 PM 模型。
- 尾巴和衣服组合以 Unity Prefab / Animator 为准，不能只看 FBX 中有哪些网格。
- 参考 Addon 只学习比例、裁切、骨架和权重方法，不复制它的网格或贴图。
- 同一技术路线最多尝试三次，继续失败就恢复已验收基线并更换路线。
- 模型、材质或 Lua 更新后必须完整重启 GMod，并删除旧 NPC / Ragdoll 后重新生成。

完整项目请按 [`references/review-checklist.md`](references/review-checklist.md) 逐项截图验收。

## 运行环境

- Windows 10/11
- Garry's Mod 和 Source 模型编译工具
- Blender 与 Blender Source Tools
- Python 3
- StudioMDL / HLMV / GMad
- VTFEdit Reloaded 或 VTFCmd
- GLuaLint

具体路径由 Skill 在任务开始时搜索，不应直接照搬旧项目的绝对路径。

## English

`gmod-model-porter` is a Codex Skill for producing and validating complete Garry's Mod character addons from Blender, FBX, Unity packages, and VRChat avatars.

It covers player models, dedicated friendly/hostile NPCs, physics ragdolls, three C-Arms variants, bodygroups, Source materials, jigglebones, measured hitboxes, facial flexes, automatic blinking, closed eyes on death, GMA packaging, and checksum-verified deployment.

Invoke it in a new Codex task with:

```text
$gmod-model-porter Port this character as a complete Garry's Mod addon and validate it in game.
```

## Credits and asset policy

The workflow was refined while porting a Kaguya model created by IKUSIA. All original character assets remain the property of their respective authors. This repository contains no original model or texture assets and grants no redistribution rights for third-party content.
