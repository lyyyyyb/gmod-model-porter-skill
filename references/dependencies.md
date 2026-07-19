# 依赖与安装

仓库只提供流程、检查脚本和纯文本模板，不捆绑 Blender、Valve 工具、插件、模型或贴图。第三方程序应从作者或游戏平台的官方来源安装，避免把来源不明的 EXE/DLL 上传到公开仓库。

## 必需工具

| 工具 | 用途 | 建议版本 | 获取位置 |
| --- | --- | --- | --- |
| Windows 10/11 | Source 工具和 GMod 的运行环境 | 64 位 | 系统自带 |
| Garry's Mod | 提供目标游戏、`StudioMDL`、`HLMV` 和 `GMad` | Steam 当前正式版 | [Steam](https://store.steampowered.com/app/4000/Garrys_Mod/) |
| Blender | 网格、骨架、权重、Shape Key、C-Arms 和自动审查 | 项目实测 5.0.1；旧插件不兼容时使用 4.1/4.2 LTS | [blender.org](https://www.blender.org/download/) |
| Blender Source Tools | 从 Blender 导出 SMD/DMX/VTA | 与当前 Blender 兼容的最新版 | [官方站点](http://steamreview.org/BlenderSourceTools/) |
| Python | 运行工作区、QC、Addon、状态和哈希检查脚本 | 3.10 或更高；项目实测 3.14.5 | [python.org](https://www.python.org/downloads/windows/) |
| StudioMDL | 按 QC 编译 `.mdl/.vvd/.vtx/.phy` | 随 GMod 安装 | `GarrysMod/bin/studiomdl.exe` |
| HLMV | 在进游戏前检查动作、身体组、材质、Hitbox 和 Flex | 随 GMod 安装 | `GarrysMod/bin/hlmv.exe` |
| GMad | 创建并反向解包 Workshop GMA | 随 GMod 安装 | `GarrysMod/bin/gmad.exe` |

Blender 5.0.1 是本次完整角色项目实际使用的版本，不代表所有 Blender Source Tools 版本都兼容 5.0。若导出插件无法启用，先换到插件明确支持的 Blender LTS，不要在同一环境连续修补三次。

## 推荐工具

| 工具 | 用途 | 获取位置 |
| --- | --- | --- |
| Crowbar | QC 编译界面、模型反编译和日志查看 | [Steam Group](https://steamcommunity.com/groups/CrowbarTool) |
| VTFEdit / VTFCmd | 生成 VTF、Mipmaps、法线图和批量转换 | [Valve Developer Community](https://developer.valvesoftware.com/wiki/VTFEdit) |
| GLuaLint | 检查 GMod Lua，避免普通 Lua 解析器误判 GLua | [GitHub](https://github.com/FPtje/GLuaFixer) |
| 7-Zip | 检查和提取 UnityPackage 等归档 | [7-zip.org](https://www.7-zip.org/) |
| AssetRipper | 在许可允许时检查 Unity 项目资源、Prefab 和材质 | [GitHub](https://github.com/AssetRipper/AssetRipper) |
| Git | 获取 Skill、保存模板修改历史 | [git-scm.com](https://git-scm.com/download/win) |

## 可选工具

- Unity Hub/Editor：只有需要准确读取 Prefab、Animator、材质或 PhysBone 组件时才安装对应项目版本。
- Blender MCP：适合实时观察场景和交互调整；关键修改仍应保存成 Blender Python 脚本和编号 `.blend`。安装第三方 MCP 前先审查其仓库、权限和网络配置。
- 图像编辑器：用于检查透明通道、法线图和贴图边缘；不应以截图覆盖原贴图来掩盖材质问题。

## 自动检测

在仓库根目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_dependencies.ps1
```

输出 JSON 报告：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_dependencies.ps1 `
  -JsonPath reports\dependencies.json
```

检测器只读取 PATH、Steam 库、Blender 用户插件目录和常见工具目录，不下载程序、不修改 PATH。加 `-Strict` 后，只要必需工具缺失就返回失败，适合自动验收。

## 安装顺序

1. 用 Steam 安装并至少启动一次 Garry's Mod。
2. 安装 Blender；为旧工程保留兼容版本，不要直接覆盖唯一可工作的版本。
3. 在 Blender 中安装并启用 Blender Source Tools，确认能看到 Source Engine 导出选项。
4. 安装 Python，并勾选加入 PATH。
5. 按需安装 Crowbar、VTFEdit Reloaded、GLuaLint、7-Zip 和 AssetRipper。
6. 运行依赖检测器，确认必需项没有 `MISSING`。

## 不应上传的文件

- Blender、Crowbar、VTFEdit、Valve 工具的 EXE/DLL。
- Valve 默认模型、动画、DMX/SMD、材质和贴图。
- 参考 Addon 的 C-Arms、骨架网格或反编译产物。
- 原作者模型、付费 Booth/VRChat/Unity 资源及其贴图。
- 包含用户绝对路径、Steam 账号或未发布项目名的构建日志。
