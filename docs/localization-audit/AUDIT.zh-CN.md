# MuMain v1.37.0 简体中文本地化审计

审计日期：2026-11-08。基线：官方标签 `v1.37.0`，提交 `07720990fc3ebb30560050a2e191af6dba089abf`。
源码在现有客户端旁的 `source-v1.37.0`，独立分支 `localization/zh-CN-v1.37.0`。
审计依据为本标签代码和 `docs/translation-system.md`、`docs/build/windows/{console,visual-studio}.md`，不是 GitHub main 的后续状态。

## 资源基线（修改前）

| 类别 | 英文条目/名称组 | 已有 zh-CN | 缺失 |
|---|---:|---:|---:|
| Game | 3148 | 255 | 2893 |
| Dialog | 233 | 0 | 233 |
| Editor | 1417 | 0 | 1417 |
| Metadata | 59 | 0 | 59 |
| 物品名称 | 911 | 1 | 910 |
| 怪物名称组 | 314 | 0 | 314 |
| NPC 名称组 | 101 | 0 | 101 |
| 陷阱名称组 | 7 | 0 | 7 |
| other 名称组 | 1 | 0 | 1 |

物品统计排除 11 个无 name 的保留条目。怪物按 JSON 名称组计数，不把共享名称的多个数字 ID 当成不同译文；完整 ID 对照见 `baseline/names.tsv`。空白的历史占位名称也保留在清单中，不虚构译名。
全部资源组共缺 4602 项；玩家界面 Game + Dialog 缺 3126 项。Editor/Metadata 属于编辑器功能，优先级低于玩家界面。

## MU Helper 的英文来源

`src/source/UI/MuHelper/{MuHelperConfigWindow,MuHelperDetailWindow,MuHelperSkillPicker}.cpp`、
`src/source/UI/HUD/MuHelperBar.cpp` 和 `src/source/MUHelper/` 共引用 **65 个不同 Game 键，缺 62 个中文值**。
逐条英文、资源键和原有中文见 `baseline/helper.tsv`。

- 标题、战斗/拾取页、药水、回血、技能条件、队伍辅助、拾取、保存/初始化及快捷栏已经使用 `I18N::Game`。
- 缺值后由生成的 C++ 表回退英文；改 `config.ini` 或直接把 resx 放在 Main.exe 旁边无法补齐已编译表。
- 技能选择器还读取 `SkillAttribute[].Name`，来自 Skill BMD；补齐 Helper 的 62 个资源键不会自动汉化技能名。
- `l.seconds = "s"` 是硬编码时间单位，非缺失资源键；可保留标准单位，避免为单位改动界面控制逻辑。
- `GameLogic/Automation/HelperPickupFilter.cpp` 用物品**显示名称**匹配用户自定义拾取关键词。中文物品名启用后，旧英文关键词可能不再匹配。不得偷偷改匹配逻辑；使用时按显示名称更新关键词，或关闭“翻译物品名称”。

## 数据来源和修改边界

| 内容 | 实际来源 | 计划 |
|---|---|---|
| 物品名 | `src/bin/Data/Items/Group*.json` 的 name | 只新增 zh-CN；保留全部数值、ID、英文、技能绑定 |
| 怪物/NPC 名 | `src/bin/Data/Monsters/Monsters.json` 的 name | 只新增 zh-CN；不改 model、kind、numbers、地图 |
| 转职 NPC 对话/回答 | `Dialog.*.resx`，`GameLogic/Quests/QuestDialog*` | 新建 Dialog.zh-CN，键与回答槽位原样保留 |
| 技能名称 | `Data/Local/<Language>/Skill_<Language>.bmd` | 与 UI Locale 独立；先审计，不篡改二进制技能属性 |
| 任务标题 | `Quest_<Language>.bmd` | 与 UI Locale 独立，不能仅靠 Dialog 翻译覆盖 |
| 扩展任务正文 | `QuestWords_<Language>.bmd` | 与 UI Locale 独立；需要保留任务 ID 和变量的文本层方案 |
| 大师技能说明 | 固定加载 `Data/Local/Eng/MasterSkillTooltip_eng.bmd` | 即使改 LOGIN Language 仍可能英文 |
| 系统提示 | Game + 服务端消息 + 少量 C++ 字面量 | 翻译客户端资源；服务端直接发送的英文原文不改 |
| 地图标题图/小地图 | `Data/Local/<Language>` 图片/数据 | 字体设置不能翻译图片 |

本机安装数据只有 Eng/Por/Spn；不擅自改 `[LOGIN] Language` 为不存在的中文目录。旧 `Text`/`Dialog` BMD 不是现行界面翻译入口。

## 硬编码审计

扫描全部 C++ `.cpp/.h` 得到 **3618 处含拉丁字母的宽字符串候选，分布于 176 个文件**。
这是可复查候选数量，不是“3618 个漏翻界面文本”：大量条目是路径、格式串、诊断、协议/命令或编辑器专用内容。
`baseline/wide-literal-candidates.tsv` 包含位置和上下文，`baseline/game-call-sites.tsv` 包含资源使用位置。

已人工确认的玩家可见硬编码：

- `UI/Dialogs/CustomMessageBox.cpp:96` 默认 `OK` 按钮。
- 同文件约 1400 行幸运物品兑换标题为韩文（功能在 README 中仍列未完成，不顺带改业务）。
- `Network/Server/WSclient.cpp:400,417` 连接失败正文/标题。
- `Dotnet/Connection.cpp:168` 的 `Network Error` 标题。
- `App/Platform/Windows/Winmain.cpp` 的应用/渲染器错误标题。

还需区分 RML 模板正文、C++ 窄字符串和格式化后文本，单靠宽字符串正则不能证明“全部界面已覆盖”。优先处理普通玩家流程；技术日志、文件路径、资源标识、调试命令保持原样。

## Windows 编译条件

本机 PATH 未找到 cmake、ninja、dotnet、cl、msbuild、gh；标准安装目录未找到 Visual Studio C++ 工具链、.NET SDK 或 vcpkg。
已找到随 Codex 分发的 Python，可运行 XML/JSON、格式占位符、结构差异和字体覆盖静态检查。
现有 Main.exe 是原版 v1.37.0，不是本次汉化构建。

官方原流程使用 MSVC + .NET 10 NativeAOT + CMake/Ninja + vcpkg，并构建 ResxGen。
`.github/workflows/ci.yml` 有 Windows x64 无编辑器构建；`fork-ci.yml` 为手动编辑器构建但不上传产物。
可复用 Windows job 的配置，增加手动本地化构建和 artifact 上传，不启用发布、不更改 OpenMU 协议。
当前没有可写远程仓库/已认证 Actions 执行环境，不能把“准备好 workflow”当成“已编译”。

## 执行顺序及验收

1. 保存审计和原文件，按模块提交。
2. 补齐 MU Helper 及共享操作资源；补充常见物品、怪物、NPC 的可靠中文名。
3. 按模块补任务对话、技能/系统提示；未确认的专有名词保留原文并列入复核清单。
4. 校验 XML/JSON UTF-8、重复键、英文键集合、printf/花括号占位符、命令、纯文本修改边界、字体覆盖。
5. 实际 Windows 构建后才验证 Main 启动、两种主题、75%/150% 缩放、语言切换、挂机选项、原配置连接 OpenMU 0.10.1。

本报告为第一阶段基线；实施后的覆盖率、构建和实机状态另行记录，不能以静态通过替代游戏实测。
