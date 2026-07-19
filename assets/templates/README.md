# 模板说明

这些文件是公开仓库自制的通用骨架，不含角色、Valve 或参考 Addon 的网格、动画、贴图和二进制。

- `port-config.example.json`：项目目标、路径、许可和交付范围。
- `source-manifest.example.json`：记录作者、来源、许可、输入文件用途和 SHA256，默认禁止再分发。
- `blender/setup_port_scene.py`：从空白场景生成标准集合和 72 单位目标配置，不含任何模型资产。
- `blender/inspect_character.py`：只读统计 Blender 场景、网格、骨架、材质、Shape Key、权重和边界。
- `player.qc`、`npc_female_citizen.qc`、`carms.qc`：PM、独立 NPC 和 C-Arms 编译起点。
- `material_character.vmt`：角色材质起点；透明、双面、法线和 Phong 必须按原材质决定。
- `jigglebones.qci`：按 Unity PhysBone 或 Dynamic Bone 实测值填写的单链模板。
- `hitboxes.qci`：按人体加权网格测量的 Hitbox 骨架。
- `lua/`：PM、三套 C-Arms、敌友 NPC、Ragdoll 和死亡闭眼注册起点。
- `addon.json`、`workshop_description_zh_en.txt`：Addon 和 Workshop 发布文本起点。

运行 `scripts/create_port_workspace.py` 创建工作区；它会生成项目配置、来源清单和 Workshop 说明副本，再把其余需要的模板复制到工作区。任何 `{{TOKEN}}` 未替换时都不得编译或发布。
