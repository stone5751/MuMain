# 构建、安装和验收说明

本分支基于官方 MuMain **v1.37.0**，目标为 Windows x64 玩家客户端。
截至 2026-11-08，只完成资源生成器编译、资源校验和静态检查；**尚未编译 Main.exe，也未完成游戏内或 OpenMU 0.10.1 连接测试**。
原有 Main.exe 不代表本分支构建。完整结果见 `RESULTS.zh-CN.md`。

## 两种交付物的区别

- `MuMain-v1.37.0-zh-CN-data-only.zip`：仅含新增中文名称的 JSON 和说明，无可执行文件。不会改变 MU Helper 或其他已编译界面文字。
- `MuMain-v1.37.0-zh-CN-windows-x64-update.zip`：仅在手动 GitHub Actions 成功后生成，包含新 Main.exe、DLL、着色器、名称 JSON 和构建标记。当前尚未生成。它是基于原版 v1.37.0 的更新包，仍需要已有的合法 Data、fonts 等客户端资源。

两者都不携带 config.ini；服务器地址、端口、账号及原有设置由现有配置控制。不要把源码 resx 直接放到 Main.exe 旁期望界面生效，必须重新编译。

## 本地构建

首先按 `docs/build/windows/console.md` 安装 Visual Studio C++ x64/Windows SDK、Ninja、CMake、.NET 10、vcpkg 和项目依赖。在 **Visual Studio x64 Developer PowerShell** 中设置 VCPKG_ROOT，然后在仓库根目录执行：

```powershell
python -m pip install fonttools==4.61.1
python scripts/validate_zh_cn.py
./scripts/build_zh_cn.ps1 -CheckOnly
./scripts/build_zh_cn.ps1
```

脚本复用 `windows-x64` / `windows-x64-release` 预设，禁用编辑器和控制套接字。资源生成是构建的一部分。
默认输出在 `out/build/windows-x64/src/Release`，依照项目原文档准备运行数据及动态库。
本机已临时准备 .NET SDK/CMake 用于验证；仍缺 MSVC、Ninja、vcpkg，预检查因此失败，未进行原生构建。

## GitHub Actions 备选

`.github/workflows/zh-cn-windows.yml` 复用项目现有 Windows runner、工具链、vcpkg 缓存和编译配置。
在你拥有写权限的 fork 中推送此分支，然后手动运行 **Simplified Chinese Windows x64**。如 GitHub 要求，先将 workflow 文件加入 fork 的默认分支，再选择本地化分支运行。
它校验资源、编译 Release、运行原生 CTest，检查 PE 为 x64，然后上传更新 ZIP；不创建 Release、不自动部署、不修改 NAS。
当前只验证了 YAML/PowerShell 语法；尚未推送或执行远程工作流。runner 可用性、依赖下载和最终链接仍需实际构建确认。

即使 Actions 成功，`localization-build.txt` 仍会明确标记 `in-game-and-openmu-connection=NOT-TESTED`，不能用 CI 成功代替联网验收。

## 安装与回退

1. 退出客户端。复制完整原客户端目录作为备份，至少保留 Main.exe、DLL、shaders、Data/Items、Data/Monsters、config.ini。
2. 建议先在客户端副本上解压相应更新包，覆盖同路径文件。保留原 config.ini 和原有 BMD/其他 Data 文件。
3. 配置保持 `[UI] Locale=zh-CN`、`Font=Noto Sans SC`。物品名还受“翻译物品名称”设置控制。
4. MU Helper 自定义拾取按**显示名称**做包含匹配。原英文关键词需要改成当前中文名称，或关闭“翻译物品名称”；不要在验证前直接依赖旧关键词进行挂机。
5. 回退时恢复备份。切回英文 Locale 可验证英文界面及名称；配置的具体保存方式遵循客户端原有设置机制。

当前工程没有覆盖、停止或重新启动原客户端，没有触碰 NAS 服务端和数据库。

## 尚待执行的验收记录

| 项目 | 操作及通过标准 | 当前状态 |
|---|---|---|
| 原生构建 | Windows x64 Release 编译、链接，CTest 通过 | 未执行，工具链缺失 |
| 冷启动 | 保留原配置正常启动，无资源/DLL错误 | 未执行 |
| 字体与布局 | Noto Sans SC；旧/现代主题；75%/100%/150%；无方块、遮挡、不可达按钮 | 字形覆盖通过；只有 HTML 静态预览，实机待测 |
| Helper | 三页、详情、技能选择、保存/重开、初始化、快捷栏 | 资源键齐全；交互待测 |
| 切换语言 | Helper 打开与关闭时切换 zh-CN/en，重开详情，无旧文案残留、不丢暂存设置 | 已修改缓存刷新代码；未编译/运行验证 |
| 物品/怪物/NPC | 地面、背包、商店、提示框显示一致；英文可切回 | JSON 静态校验通过；实机待测 |
| 技能/任务 | 描述与对话中文；记录仍从 BMD 读取的英文 | BMD 名称和正文未翻译 |
| 拾取回归 | 中文关键词、英文模式关键词、过滤分类与原版行为一致 | 待测 |
| OpenMU 0.10.1 | 原地址端口登录、选角、移动、打怪、拾取、NPC交互 | 未执行；不宣称兼容性已验证 |

静态预览使用项目的 RML→HTML 工具，并非游戏 RmlUi 渲染器。旧主题技能标签已缩短，但固定位置的文字拥挤和预览底部重复框仍需实机确认；没有为模拟预览改动游戏布局或逻辑。
