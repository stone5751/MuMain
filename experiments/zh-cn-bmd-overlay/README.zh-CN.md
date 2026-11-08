# BMD 中文覆盖层：独立离线实验

**不是客户端补丁，不要复制进 Data。** 当前实现为 UTF-8 JSON 覆盖表和只读验证程序，客户端尚不加载它。没有改写 BMD，没有将实验代码接入稳定版。它不能让游戏里的技能/任务变成中文，也不能证明游戏内稳定性。

在源码根目录执行（Python 3，无额外依赖）：

```powershell
python experiments/zh-cn-bmd-overlay/verify_overlay.py --data D:/Downloads/MuMain/client-zh-CN-round3-test/Data --output D:/Downloads/MuMain/localization-output/round3/p2-offline-validation.json
```

程序复用已有只读提取器，先核对三份英文 BMD 的 SHA-256，再核对种类、ID、英文原文，按当前语言返回中文或原文。拒绝不同文件版本、重复 ID、超出已知运行时容量及段落分隔符变化。不会写入输入文件；结果另存为 JSON。

样本：技能 2/3/4（陨石术、掌心雷、火球术）；旧转职任务标题 0/1（寻找帝王之书、奇迹大陆的三种宝物）；QuestWords 显式 ID 2/15/16（三条新手教学文字）。技能术语与既有技能书名称一致；转职标题参考[大陆官方转职资料](https://mu.zhaouc.com/Guide/GameSystem/08_quest.html)，不采用网页的数值修改客户端。

## 已确认的加载与显示路径

| 文本 | 加载和编码 | 稳定对应关系 | 显示入口 |
|---|---|---|---|
| 技能 | `SkillDataLoader::LoadFormat` 校验 0x5A18 校验和、逐条 BuxConvert，`CopySkillAttributeFromSource` 按 UTF-8 转宽字符 | 本机文件 650×108+4 字节，名称50字节；记录索引就是技能 ID，前三个样本与 `_enum.h` 显式枚举核对 | `SkillManager::GetSkillInformation` 及其他直接读取 `SkillAttribute[id].Name` 的调用 |
| 旧转职标题 | `CSQuest::OpenQuestScript` 逐条 BuxConvert，UTF-8 转换；原始32字节名称进入32个 wchar_t 缓冲区 | 本机200×744字节，每条名称偏移6；索引对应任务状态索引，0为 `QUEST_CHANGE_UP_1` | 三个 `getQuestTitle*` 接口；NPCQuest 模型读取标题 |
| 新任务正文 | `CQuestMng::LoadQuestWordsScript` 解密6字节头（int ID + short长度），再解密文本并按UTF-8转换 | 显式文本ID；**不是任务ID**。NPCDialogue/QuestProgress记录引用这些ID | `GetWords` → NPC/玩家正文、标题、摘要/回答；任务窗口按像素分行并缓存 |
| 顶部提示 | `SlideTicker::OpenSlideTextFile` 解密 SLIDEHELP，再作UTF-8转换 | 当前为等级块/文本槽位；须增加原文及文件身份校验，不能仅靠排列顺序跨版本套用 | SlideWindow / SlideTicker |

路径由 `g_strSelectedML`（旧数据语言 Eng/Por/Spn）选择，与 UI Locale 分离。把 UI Locale 改成 zh-CN 不会自动寻找中文 BMD。当前文件布局经过大小和哈希约束，不能把这里的固定偏移泛化到其他客户端版本。技能加载器还支持32字节名称的旧格式，本实验未覆盖该格式。

## 接入客户端前的风险与建议

1. **优先在显示层查找覆盖，不重写结构或二进制。** 保留原文，按 `(种类, ID, 原文)` 查找；缺少条目、非中文、原文不符时返回原文。覆盖文件只存文字，不包含属性或协议字段。加载一次，热路径不得逐帧读文件。
2. 技能名被多个位置直接读取，不能只改某一个提示框就声称技能名全覆盖。将中文直接写进全局 SkillAttribute 会污染编辑器保存/导出路径；应提供显示名访问器并限定首批调用范围。此处需要独立实现和回归测试，未实施。
3. 旧任务标题接口返回可写指针，直接返回只读资源指针会改变接口契约；应改为只读显示接口或独立、有生命周期保证的显示缓存。不能用强制类型转换绕过。
4. QuestWords 可在 GetWords 处选择原文或覆盖，保持 map 原文不变；但任务窗口已缓存分行/页码，语言切换后必须刷新这些显示缓存。不能通过重载任务进度数据实现翻译，避免影响当前任务状态。
5. 既有提取结果中部分任务正文含无效 UTF-8 字节，继续保留英文/原始数据并隔离复核。没有强行转码或替换。段落分隔符、占位符、页宽及字形均须保留/验证；MVP特意不纳入格式占位符。
6. 初次客户端试验应只启用8条样本，在独立副本验证技能提示、Helper技能选项、任务标题/正文、中英文切换与关闭重开窗口。需可触发相应任务的角色状态；不能为验收修改服务器数据库或角色数值。

## 验证边界

- 已实现：8条覆盖 JSON、只读查找/验证程序。
- 已通过：真实本地 BMD 的身份/ID/原文匹配、UTF-16容量、英文及其他语言回退、未知 ID/变更原文回退；3个异常输入拒绝检查；输入文件哈希不变。
- 未实现：客户端显示访问器、运行时加载与缓存刷新。
- 未测试：原生客户端集成编译、游戏内技能/任务显示、布局、实时切换和任务操作。不能作为可安装 BMD 汉化包交付。
- 稳定版 P0/P1 更新 ZIP 不含此目录或任何 BMD 修改。达到上述客户端验证条件前不扩大样本，也不并入稳定版本。
