# OpenMU v0.10.1 服务端消息汉化方案（未实施）

本轮只读审计官方源码，未连接 NAS、修改数据库、重启或部署服务端。审计版本为 v0.10.1，提交 `dd4352811c0a55ae8855d8df9784f53112c22231`。以下步骤供后续独立服务端任务使用，不是已经执行的操作。

## 机制和当前限制

`PlayerMessage.resx` 有 331 个键，发布源码另有 de、pt 语言资源，未提供 zh-CN。界面本地化与这些消息是两条独立路径：MuMain 的 UI Locale 不会自动修改服务端 Player.Culture。[消息资源](https://github.com/MUnique/OpenMU/blob/v0.10.1/src/GameLogic/Properties/PlayerMessage.resx)

`GetLocalizedMessage` 用资源键和 `player.Culture` 查询 ResourceManager，再将参数代入文本；蓝色和金色消息共用此机制。新增部分 zh-CN 键后，缺少的键可按 .NET 资源回退规则保留中性英文，英文资源无需改动。[消息访问器](https://github.com/MUnique/OpenMU/blob/v0.10.1/src/GameLogic/PlayerMessageExtensions.cs)

普通玩家可用 `/language` 查看已部署资源的语言，用 `/language zh-CN` 选择完整文化代码。该版本命令只赋值 `player.Culture`，没有写回 `Account.LanguageIsoCode`，所以不能当作持久化设置。语言列表存在静态缓存，部署新增卫星程序集后应重启新测试进程再检查；本轮没有运行此命令。[语言命令](https://github.com/MUnique/OpenMU/blob/v0.10.1/src/GameLogic/PlugIns/ChatCommands/ChangeLanguageChatCommandPlugIn.cs)、[可用语言缓存](https://github.com/MUnique/OpenMU/blob/v0.10.1/src/DataModel/CultureHelper.cs)

登录绑定账号时，Player 只按两字母/三字母语言代码匹配账号字段，未比较完整 `CultureInfo.Name`。因此直接把账号字段写成 zh-CN 并不能可靠选择简体中文；只写 zh 又可能依赖枚举顺序。账号字段默认 en，改容器默认区域也不会自然覆盖这个账号偏好。[Player 的 Account setter](https://github.com/MUnique/OpenMU/blob/v0.10.1/src/GameLogic/Player.cs)、[账号语言字段](https://github.com/MUnique/OpenMU/blob/v0.10.1/src/DataModel/Entities/Account.cs)

## 建议分两步实施

第一步只加资源，在隔离服务端副本中验证当前会话语言，不改账号记录。

1. 从同一 v0.10.1 提交建立独立服务端分支。确认它与实际容器构建来源一致；本轮未检查 NAS 镜像摘要。
2. 新建 `src/GameLogic/Properties/PlayerMessage.zh-CN.resx`，从现有 ResX 文件保留标准头，仅放入以下 5 个键。保留中性英文文件、资源键、参数顺序、ID 和 NPC 参数值。

| 键 | 建议中文 |
|---|---|
| InventoryFull | 背包已满 |
| TalkingNotImplementedFormat | 该 NPC（{0}，{1}）的对话尚未实现。 |
| AvailableLanguagesCaption | 可用语言： |
| RequestedLanguageNotFound | 未找到语言“{0}”。 |
| LanguageChanged | 语言已切换为“{0}”（{1}）。 |

NPC 参数 `{1}` 来自服务端定义；翻译整句后它仍可能是英文。不要在消息格式化层替换玩家名、NPC ID 或任意聊天内容，也不要把“尚未实现”改成“连接错误”。

3. 在有 .NET 10 SDK 的独立构建环境执行（仅是后续命令示例）：

```powershell
dotnet build src/GameLogic/MUnique.OpenMU.GameLogic.csproj -c Release
dotnet publish src/Startup/MUnique.OpenMU.Startup.csproj -c Release -o out/zh-cn-server-test
```

检查发布目录含 `zh-CN/MUnique.OpenMU.GameLogic.resources.dll`，并用 ResourceManager 对 zh-CN、en 和缺失键做断言。不要将 `.resx` 直接复制到运行中的容器指望热加载。项目使用 SDK 嵌入资源，原有 Startup Dockerfile 复制完整 publish 输出，且已安装 ICU 并关闭 globalization invariant；如实际镜像另有裁剪或资源语言筛选，必须再核对。[GameLogic 项目](https://github.com/MUnique/OpenMU/blob/v0.10.1/src/GameLogic/MUnique.OpenMU.GameLogic.csproj)、[官方 Dockerfile](https://github.com/MUnique/OpenMU/blob/v0.10.1/src/Startup/Dockerfile)

4. 使用隔离配置、测试数据库或批准的数据库副本启动测试服务端。验证 `/language` 出现 zh-CN，切换后触发背包满消息和不支持的 NPC，对照 en 恢复英文。不得为了测试连接生产数据库自动迁移或初始化。
5. 验证通过并获得另行部署授权后，才考虑替换正式服务容器。采用固定版本的新镜像，不向运行中容器临时拷贝单个 DLL；保留旧镜像摘要、Compose 配置和常规备份。回退恢复旧镜像；此资源阶段不需要数据库架构迁移。

第二步如需要重登记住语言，再单独修改和验证：

- Account setter 先按 `cu.Name`（OrdinalIgnoreCase）匹配，再兼容旧的两/三字母代码，最后保持原回退方式。
- `/language` 成功时，按项目已有账号持久化生命周期保存规范代码 `requestedCulture.Name`。必须核对保存是否真的落库；仅赋值属性不等于已经持久化。
- 增加完整 zh-CN、旧 en/de/pt、未知代码、重登和不同账号并行语言的测试。只涉及现有账号偏好字段，不修改角色属性、物品数据或协议。
- 这一步会改变账号偏好数据，应独立授权和记录；本轮不执行。

## 编码和长消息风险

ShowMessagePlugIn 按 UTF-8 字节数检查消息，并以 241 字节为阈值分段。短中文仍应在真实客户端检查完整显示。[消息发送代码](https://github.com/MUnique/OpenMU/blob/v0.10.1/src/GameServer/RemoteView/ShowMessagePlugIn.cs)

发现一个应在大规模服务端翻译前处理的边界：`GetCharacterCountOfMaxByteCount` 将起始字符数直接设为 maximum。100 个普通汉字为 300 UTF-8 字节，却只有 100 个 UTF-16 单位，传入 count=241 的 GetByteCount 会越界。本机只做了等价 .NET 调用复现，得到 ArgumentOutOfRangeException；未执行完整 OpenMU 单测，更未在 NAS 触发。[编码辅助方法](https://github.com/MUnique/OpenMU/blob/v0.10.1/src/GameServer/EncodingExtensions.cs)

后续修复建议：起点限制为 `Math.Min(text.Length, maximum)`，并避免截断 UTF-16 代理项；为 80/81/100 个汉字、中文夹英文、补充平面字符和连续分包添加测试。不要只靠字数限制估算 UTF-8 包长。首批 5 条应核对代入参数后的字节数；在分包边界未验证前不批量翻译长公告。

## 本轮结论

可行，优先沿用服务端 ResX + 每玩家 Culture 机制。已明确最小资源改动、会话切换、持久化缺口、发布方式和长消息边界；所有服务端修改、服务端构建、NAS 部署及实际服务端中文消息验收均为未执行。
