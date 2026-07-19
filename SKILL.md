---
name: gmod-model-porter
description: Port, repair, audit, compile, package, and deploy complete character models from Blender, FBX, Unity packages, or VRChat avatars into Garry's Mod. Use for player models, friendly/hostile NPCs, ragdolls, C-Arms, bodygroups, facial flexes and blinking, materials/VTF/VMT, jigglebones, hitboxes, QC/StudioMDL, GMA/Workshop releases, scale or weighting problems, T-poses, broken fingers, tails, clothing, lighting, and other Source model faults.
---

# GMod Model Porter

把角色转模当成一条有验收门槛的生产流程。先查清 Unity/Blender 原版的真实结构，再制作 PM、NPC、Ragdoll 和 C-Arms；不要把“能编译”当成“能交付”。

## 工作约定

1. 先读用户最新要求、截图和 `AGENTS.md`。直接修改要求就执行；只查原因时保持只读。
2. 在独立工作目录操作，不覆盖原始 `.blend`、`.fbx`、UnityPackage、贴图或已经验收的版本。
3. 先运行 `git status --short`；不要碰无关脏文件。
4. 使用 Blender Python 做可重复的网格、骨架和导出工作。Blender MCP 适合观察与交互验证，但最终关键修改必须落成脚本或明确步骤。
5. 每个里程碑运行 `scripts/checkpoint.py`，保存输入、状态、下一步、产物和失败路线。接口中断后先 `--show` 再继续。
6. 同一技术路线失败最多三次。第三次仍失败时停止打补丁，记录证据并更换网格、权重、编译或部署方案。
7. 参考其他 addon 时只学习比例、裁切、骨架、权重和 QC 方法；未经许可不得复制它的网格、贴图或成品手臂。
8. 修改前备份游戏 addon，修改后用逐文件 SHA256 比较。不要只覆盖 Lua 或单独一个 `.mdl`。

## 开始任务

1. 阅读 [workflow.md](references/workflow.md)，建立阶段计划和验收门槛。
2. 涉及异常时阅读 [diagnostics.md](references/diagnostics.md)。
3. 涉及 C-Arms、尾巴、材质、动骨、Hitbox 或 NPC 时阅读 [kaguya-lessons.md](references/kaguya-lessons.md)。
4. 编译和部署前阅读 [review-checklist.md](references/review-checklist.md)。
5. 需要定位 Blender、StudioMDL、HLMV、GMad 或 Crowbar 时阅读 [toolchain.md](references/toolchain.md)。
6. 复制 `assets/templates/` 中需要的模板，并替换全部 `{{TOKEN}}`；不得把未替换模板直接编译或发布。

## 固定工作目录

使用以下布局，阶段产物只向前流动：

```text
work/
  source_original/     原始只读文件
  source_work/         分阶段 Blend 和导出脚本
  unity_extract/       Unity prefab、材质、动画和 PhysBone 证据
  compile/             QC、SMD/DMX、VTA、PHY 源文件
  compiler_game/       StudioMDL 临时输出
  addon_stage/         待验收 addon
  release/             GMA 和发布文本
  reports/             JSON、日志、哈希和检查结果
  previews/            Blender/HLMV/GMod 验收图
  backups/             部署前备份
```

## 生产门槛

### 1. 原版审查

- 列出所有网格、材质、贴图、骨架、BlendShape、动画、身体组候选和 Unity 开关。
- 从 Prefab、Animator 和 PhysBone 还原真实默认状态。不要只根据 FBX 中“看得见的全部网格”猜身体组。
- 记录作者、来源链接、许可和删除配合声明。不要把原模型资产放入 Skill 或公共仓库。
- 明确交付范围：PM、三套 C-Arms、敌友 NPC、Ragdoll、身体组、眨眼、动骨、压缩版/未压缩版、Workshop。

### 2. 玩家模型

- 以 ValveBiped 标准骨架为动画基线，保留角色需要的辅助骨；保证父子方向和本地轴正确。
- 用脚底到头顶的实际人体高度比较 Alyx/女性参考模型。不要让尾巴、头发、耳朵或帽子参与身高计算。
- 在站立、跑步、蹲下、跳跃、持枪和 Ragdoll 姿势下检查肩、肘、腕、手指、髋、膝和脚。
- 身体组按穿衣层级拆分。关闭外套后必须露出正确 JK 层；用户要求衣服不可脱时，不提供裸身切换。
- 宠物若原版是独立跟随物，不要绑在人体骨头上伪装；无法还原时删除。

### 3. 材质与外观

- 为每个材质建立唯一稳定路径，检查 VMT 中所有 VTF 引用和大小写。
- 未压缩版保留原分辨率和合理无损/高质量 VTF；压缩版单独构建，不能反向覆盖母版。
- 双面需求使用正确法线并在需要的 VMT 中设置 `$nocull 1`。透明、裁切、自发光和法线图分别处理。
- 黑灰变纯黑时先检查色彩空间、VTF 格式、法线标记、Phong 强度和颜色乘数；不要用全局提亮掩盖错误。
- 通过 PM、NPC、Ragdoll、C-Arms 四个入口检查材质，不以 Blender 视口作为最终证据。
- 将活体自动眨眼和死亡闭眼分开验收；Ragdoll 创建时对 PM/NPC 模型设置 `blink=1`，不得用持续全图扫描。

### 4. 动骨与 Hitbox

- 从 Unity PhysBone 的链、根节点、限制和默认姿势映射到 `$jigglebone`，按头发、裙摆、耳朵、袖口、尾巴分别调参。
- 不把胸部动骨当默认功能；只有用户明确要求并通过姿势验收才保留。
- 多尾模式必须保持独立尾链和正确扇形默认姿势；单尾身体组只能包含一条尾巴，不得叠加九尾网格。
- Hitbox 根据加权人体网格的骨骼局部边界制作，覆盖头顶、躯干、手臂、手掌、腿和脚；排除头发、尾巴、帽子和挂件。

### 5. C-Arms

- 保留角色自己的手掌、手指、指甲、UV、法线和材质；参考 addon 只用于理解裁切和变换。
- 使用标准 47 骨 C-Arms 骨架，不修改骨头位置来迁就网格。
- 同时制作自动、裸手和 JK 袖三套。厚外套第一人称默认切到裸手；JK 身体组应切到 JK 袖手模。
- 在已验证权重上做局部几何调整。不要整体重算手指权重；普通四指逐节检查，拇指单独处理。
- Blender 弯曲图只能证明破面压力，不等于真实持枪效果。最终必须在 GMod 用拳头、物理枪、工具枪、手枪和步枪验收。

### 6. 编译与注册

- PM QC 使用 `f_anm.mdl`；女性 Citizen NPC 必须编译独立 `models/npc/...` 模型，并包含四套 `humans/female_*` 动画。
- 不得让 NPC Lua 直接使用 `models/player/...`，否则常见结果就是 T 字。
- PM/NPC/Ragdoll 模型检查 `.mdl`、`.vvd`、`.phy`、`.dx80.vtx`、`.dx90.vtx`；C-Arms 至少检查 `.mdl`、`.vvd` 和 VTX。
- Lua 分别注册 PM、Hands、Friendly NPC、Hostile NPC 和 Ragdoll。NPC 使用专用 `NPC_MODEL`，旧地图实例必须删除后重建。
- 对所有 Lua 运行 GLuaLint，对 QC 运行 `scripts/audit_qc.py`，对 addon 运行 `scripts/audit_addon.py`。

### 7. 部署与发布

- 先关闭 GMod 或明确要求用户完整重启。模型、材质和 Lua 会被缓存，热覆盖不能作为验收。
- 将旧 addon 复制到工作目录 `backups/`，核对备份文件数后再完整替换目标 addon。
- 使用 `scripts/audit_addon.py --compare` 验证源目录和游戏目录零差异。
- 用 GMad 创建 GMA，再反向解包到空目录并逐文件比较；确认 GMA 不包含 QC、Blend、源贴图、日志或备份。
- 游戏内重新生成 PM、NPC 和 Ragdoll，按 [review-checklist.md](references/review-checklist.md) 截图验收。

## 自动工具

```powershell
python scripts/checkpoint.py --work-root <work> --task "Port model" --status source-audited --next "Build PM"
python scripts/audit_qc.py --qc <player.qc> --kind player
python scripts/audit_qc.py --qc <npc.qc> --kind npc
python scripts/audit_addon.py --addon <addon_stage> --glualint <glualint.exe> --json <report.json>
python scripts/audit_addon.py --addon <addon_stage> --compare <game_addon>
```

任何自动检查通过都不能替代游戏内动作验收。报告必须区分“文件验证通过”和“已在 GMod 验收”。

## 完成标准

- 给出功能结果、仍有限制、部署位置、备份位置、文件数、哈希差异、编译/Lua 检查和是否完成游戏内验收。
- 明确说明是否修改了压缩版、未压缩版、GMA、最终仓库和游戏 addon。
- 最后给非程序员一条可以照做的操作：完整退出并重启 GMod，删除旧实例，重新生成指定 PM/NPC/Ragdoll，再按指定武器和身体组截图。
