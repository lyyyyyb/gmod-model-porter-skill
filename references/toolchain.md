# 工具链与执行方式

安装、版本建议和官方下载位置见 [dependencies.md](dependencies.md)。仓库只保存脚本和纯文本模板，不保存第三方可执行文件、Valve 资源或角色资产。

## 工具选择

优先使用仓库已提供的 Blender 版本、插件、模板和 Source 编译工具。不要先升级 Blender 或插件；旧项目常依赖特定版本的 Blender Source Tools。

常用工具：

- Blender + Blender Source Tools：网格、骨架、权重、Shape Key、SMD/DMX/VTA 导出。
- Blender Python：可重复批处理、审计、渲染和编号保存。
- Blender MCP：观察场景、交互检查和用户要求的实时操作；关键修改仍保存为脚本/Blend。
- Crowbar/StudioMDL：QC 编译、反编译参考模型、查看编译日志。
- HLMV：动作、身体组、材质、Hitbox、Flex 和附件预览。
- VTFEdit Reloaded/VTFCmd：VTF 创建、格式和 Mipmap。
- GLuaLint：GMod Lua 语法和静态检查。
- GMad：GMA 创建和反向解包。
- `rg`、PowerShell、SHA256：路径搜索、清单、部署核对。

## 路径发现

先运行统一检测器，不写死旧项目路径：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_dependencies.ps1 `
  -JsonPath <work>\reports\dependencies.json
```

检测器搜索 PATH、Steam 库、Blender 用户插件目录和少量常见工具目录，不会递归扫描整盘，也不会下载程序或修改 PATH。

## 项目初始化

```powershell
python scripts\create_port_workspace.py `
  --work-root <work> `
  --model-id <model_id> `
  --display-name "<Display Name>" `
  --target-height 72
```

脚本只创建目录、项目配置和恢复状态，不复制原模型。源文件许可确认后，另行复制到 `source_original/`，后续修改只写入 `source_work/`。

## Blender 后台执行

将每个阶段写成幂等或输出编号文件的脚本：

```powershell
& <blender.exe> --background <input.blend> --python <step_script.py>
```

脚本要求：

- 输入/输出使用绝对路径或从脚本位置解析。
- 开始前检查预期对象、骨架和版本，缺失时直接失败。
- 不覆盖输入 Blend。
- 输出编号 Blend、导出目录、JSON 审计和必要预览。
- 报告对象数、骨数、三角面、Shape Key、权重异常和文件哈希。

需要 GUI/MCP 时，每次操作后保存编号 Blend；连续三次无法稳定完成时切回后台 Python。

没有许可明确的 `Workspace.blend` 时，生成一个不带骨架、模型或贴图的干净工作模板：

```powershell
& <blender.exe> --background --factory-startup `
  --python assets\templates\blender\setup_port_scene.py `
  -- --output <work>\source_work\00_workspace.blend --target-height 72
```

第一次处理未知 Blend 时先运行只读清单模板：

```powershell
& <blender.exe> --background <input.blend> `
  --python assets\templates\blender\inspect_character.py `
  -- --output <work>\reports\blender_inventory.json
```

## StudioMDL 编译

在隔离的临时 game 目录编译，避免把半成品直接写入真实 GMod：

```powershell
& <studiomdl.exe> -game <compiler_game> <model.qc>
```

保存 stdout/stderr，并检查：

- 输出模型路径是否正确。
- 材质搜索路径和缺失贴图。
- 顶点/索引/骨/权重限制。
- Flex、VTA/DMX 规则。
- Physics Mesh 和碰撞关节。
- 动画 Include 与 Sequence。

编译成功后不要只复制 `.mdl`；复制同名的 VVD、PHY、DX80/DX90 VTX。

## QC 自动审查

```powershell
python scripts/audit_qc.py --qc <player.qc> --kind player
python scripts/audit_qc.py --qc <npc.qc> --kind npc
python scripts/audit_qc.py --qc <arms.qc> --kind arms
```

自动审查只能发现结构缺项，不能判断实际姿势、材质或 Hitbox 尺寸是否正确。

## GLuaLint

优先审查整个 Lua 目录：

```powershell
& <glualint.exe> lint <addon\lua>
& <glualint.exe> version
```

不要用普通 Lua 解析器替代 GLuaLint，因为 GLua 有自己的语法扩展。

## Addon 审查与部署比较

```powershell
python scripts/audit_addon.py --addon <staging_addon> --glualint <glualint.exe> --json <report.json>
python scripts/audit_addon.py --addon <staging_addon> --compare <game_addon>
```

只有 `errors=0` 且部署差异为 0 才进入游戏验收。

## GMA 创建与反解

```powershell
& <gmad.exe> create -folder <addon_stage> -out <release.gma> -quiet
& <gmad.exe> extract -file <release.gma> -out <empty_extract_dir> -quiet
```

比较时排除 GMad 正常忽略的 `addon.json`，其余资源必须逐文件哈希一致。GMA 内不得包含开发源文件和备份。

`assets/templates/build_release.ps1` 已实现开发文件拦截、已有发布备份、GMad 创建、反向解包、SHA256 核对和收据生成。将它复制到工作区使用，不要把输出 GMA 提交回 Skill 仓库。

## 安全部署

1. 确认目标是明确的单个 addon 目录。
2. 解析绝对路径并验证它位于预期 `garrysmod/addons` 下。
3. 将旧目录备份到工作目录 `backups/`。
4. 核对旧目录与备份文件数。
5. 删除明确目标目录并完整复制新 addon。
6. 对源/目标生成相对路径 SHA256 字典并要求零差异。
7. 不自动关闭或启动用户的 GMod，除非用户明确要求。
8. 告诉用户必须完整重启并重建旧实体。
