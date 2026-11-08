# 第三轮：日常内容覆盖与独立验证

基线为已构建提交 `6129947`。用户确认上一轮客户端功能正常；该确认不自动代表本轮新二进制通过人工验收。

## 已实施范围

- P0：`round3-game.tsv` 逐条列出270条新增文本，涵盖欢迎语、Helper运行/扣费/保存反馈、组队/战盟、交易、合成强化、属性提示、任务反馈和菜单。只补充Game简体资源，不改英文、协议或业务逻辑。
- P1：`round3-names.tsv` 逐条保留种类、完整ID组、英文名、中文名和依据。增加60组物品、22组怪物、6组NPC。写入工具同时核对ID和英文，拒绝覆盖已有中文，并保留JSON格式。来源只用于名称核对，不采用网页的属性、等级或掉落数值。
- 专有名称优先核对大陆官方资料；官方网页缺少英汉对应时，用包含明确编号或英文的资料交叉核对。普通描述性名称采用直译，映射表已明确标注，不声称全部为官方命名。不确定的条目仍保留英文。
- 原始修改前文件保留于Git基线，并在本机 `localization-backup/round3-before-6129947.zip` 留存资源备份。

## 名称依据和限制

覆盖统计：Game 1020/3148（32.4%，缺2128），Dialog 233/233（100%）；物品515/911（56.5%，缺396），怪物214/314（68.2%，缺100），NPC 63/101（62.4%，缺38）。陷阱7/7，其他1/1。

下表按现有C++调用位置中的**唯一Game资源键**统计，同一键可计入多个模块；不包含BMD、图片和网络直接文本，不能等同于整个界面的中文百分比。

| 调用模块 | 已译/引用键数 | 覆盖率 |
|---|---:|---:|
| Helper界面 | 65/65 | 100% |
| 背包与强化 | 231/232 | 99.6% |
| 商店与交易 | 26/26 | 100% |
| 角色与技能 | 88/92 | 95.7% |
| 任务界面 | 24/24 | 100% |
| 组队与战盟 | 9/10 | 90% |
| 选项 | 108/108 | 100% |
| 网络系统提示 | 112/395 | 28.4% |

常用UI统计中尚缺的6个键已逐条复查：`Julia`（NPC专名）、`Force Wave`及两个包含Dark Side/Roar/Slasher的技能伤害说明待统一技能术语；`DD1907`的值为数值格式模板，`Text2374`的值仅为斜杠，不应为提高覆盖率机械增加译文。对应列表不代表6处都有需要翻译的英文句子。

[官方坎特鲁怪物资料](https://mu.zhaouc.com/Guide/GameIntro/02_area15.html)、[官方冰霜之城资料](https://mu.zhaouc.com/Guide/GameIntro/02_area18.html)、[官方幻影寺院入口](https://mu.zhaouc.com/player/event/jzhysy/newmap.html)用于地图怪物和入口NPC术语。

[NPC历史资料](https://mu.17173.com/content/2013-03-25/20130325111945573.shtml)用于马丁、托姆绅、艾尔菲丝、奥斯本和杰瑞敦。物品的逐条双语/编号来源在映射TSV中，例如[东洋刀](https://mu.dvg.cn/v2_item_info.php?id=2329)、[雷神之剑](https://mu.dvg.cn/item_info.php?id=2340)。同系列防具根据明确的英文系列和部位组成译名，逐条保留本地ID；没有按网页排列顺序推算ID。网页后期版本出现同名或套装变体时，没有向不确定的本地变体套用译名。

## 仍可见英文的来源

1. Game缺失资源：更新后的完整键清单见 `current/missing-resources.tsv`。Editor和Metadata仍未翻译；本轮玩家包关闭编辑器。技术命令、表情动作匹配词、服务器名和格式模板不能仅因显示英文就全部替换。
2. 名称：`current/names.tsv` 中中文列为空的记录继续回退英文。包括后期专有装备、套装变体、特殊活动NPC以及空白占位。
3. 顶部操作提示：`UI/HUD/SlideWindow.cpp` 加载 `Data/Local/<语言>/Slide_<语言>.bmd`；`SlideTicker::OpenSlideTextFile` 解密后用UTF-8转换文字。它与Game资源分离，稳定包不替换此二进制。后续应和P2一起评估按稳定索引的覆盖层。
4. 聊天/公告：`Network/Server/WSclient.cpp::ReceiveChat` 将网络ChatText从UTF-8解码后显示；公告也有服务端直接文字路径。已只读核实[OpenMU v0.10.1资源](https://github.com/MUnique/OpenMU/blob/v0.10.1/src/GameLogic/Properties/PlayerMessage.resx)的 `PlayerEnteredGameMessage` 为 `{0} entered the game.`，与截图吻合。它属于服务端资源，本轮不改服务器，也不拦截玩家聊天做全局替换。
5. 技能/任务BMD、大师技能说明、图片文字、早期启动错误及未接入I18N的硬编码仍在独立范围。现有硬编码候选清单继续保留，不能把候选数当成真实漏翻数。
6. 对常用UI目录的硬编码候选复查：大量字面量其实是贴图路径、日志、格式模板。语言列表的English等本地语言名称以及字体名称应保留；字体列表Default、早期 `file corrupted.` / `file not found.` 等错误提示尚未接入本轮资源补译，不为了这些低频入口改动窗口或加载流程。

## Helper拾取与语言切换

Helper自定义拾取按显示名称的子串匹配。新增中文会使旧英文关键词不再匹配这些物品；应在游戏内根据实际显示名调整，或关闭物品名翻译。不要批量改写玩家保存的关键词。本轮不改变匹配算法。中英文名称由原有语言选择机制决定，必须实测切换；资源保留和格式检查不能证明全部窗口实时刷新。

## 验证与安装

资源验证已通过：占位符/命令、原英文、非zh-CN JSON字段、原有译文及Noto Sans SC常规/粗体字形覆盖。本轮仅新增资源和名称，不改客户端C++。

[Windows构建42468100380](https://github.com/stone5751/MuMain/actions/runs/42468100380)通过，稳定源码c9b7405：x64 Release编译链接、63项静态测试、2089项原生测试通过；2项GPU用例跳过、0失败。ZIP已核验并安装到独立第三轮副本，启动日志确认Loading ok、Noto Sans SC加载及服务器列表接收。桌面抓图仍超时；游戏内操作等待用户反馈，不能沿用上一轮结果。P2不并入此更新包。

构建期间仅调整依赖下载方式：通过Release API预取相同版本、相同SHA-256的SDL_ttf与SDL_image包，保留CMake解包、校验和补丁。第一次原生构建通过编译链接，但怪物JSON规范格式测试发现28个新增名称行末空格；已在c9b7405修正数据格式及写入工具，未改数值或跳过测试，后续重建以此提交为稳定源码。

P2独立说明和8条离线样本见 `experiments/zh-cn-bmd-overlay/README.zh-CN.md`。真实本地BMD的哈希、ID、原文、语言回退和长度/分隔符约束已通过离线验证；客户端接入尚未实施，游戏内技能/任务效果未测试。该实验不是可安装客户端补丁。

安装步骤沿用 `WINDOWS-UPDATE-README.zh-CN.md`。本机使用新的 `client-zh-CN-round3-test` 副本，保留原版及已验证的第二轮副本。config.ini只在本机复制；第三轮测试副本中将空Font设置为Noto Sans SC，先保留本地配置备份，其他字节（含地址/端口）保持不变。配置不进入Git或ZIP。回退时退出第三轮副本并运行第二轮副本；曾在游戏内保存过的Helper配置需手动恢复，复制客户端无法回退服务端保存的设置。

## 第三轮实机反馈与定点补译

用户确认进入角色、欢迎语、移动、战斗和拾取正常，截图确认助手扣费提示中文。曾出现启动助手后NPC打不开、停止后商人仍打不开；重新进入角色后恢复，再次启停助手后仍可打开。记录为一次未稳定复现的会话异常，根因未确认，没有修改NPC、助手或服务端逻辑。Helper保存、中英文切换及双主题尚未得到明确人工结果。

截图中的英文分为：

| 内容 | 确认来源 | 处理 |
|---|---|---|
| Obtained | Game资源，WSclient拾取消息后缀 | f2aac16补为“已获得” |
| 幻影导师头顶勇士对白 | Game资源，ZzzCharacter NPC闲聊 | f2aac16补为“我会助你成长为一名勇士。” |
| 顶部按D打开指令提示 | Slide_eng.bmd，只读解密核对原文 | 保留二进制；后续独立覆盖层范围 |
| Inventory is full（无句点） | OpenMU PlayerMessage.InventoryFull | 不修改服务器，不拦截聊天替换 |
| Talking to this NPC…not implemented yet | OpenMU PlayerMessage.TalkingNotImplementedFormat | 提示NPC功能未实现，不代表翻译可补出对话功能 |

[OpenMU v0.10.1消息资源](https://github.com/MUnique/OpenMU/blob/v0.10.1/src/GameLogic/Properties/PlayerMessage.resx)与[TalkNpcAction](https://github.com/MUnique/OpenMU/blob/v0.10.1/src/GameLogic/PlayerActions/TalkNpcAction.cs)只读核对，未访问或修改NAS配置/数据库。源代码中对话状态不允许推进时会拒绝新交互，但没有服务端会话证据，不能断言此次异常就是该原因。

补译源码Game为1022/3148（缺2126）；c9b7405已交付包仍为1020/3148。两条新增资源格式、占位符、既有译文保留和字体检查通过；[补译构建42471704886](https://github.com/stone5751/MuMain/actions/runs/42471704886)结果以实际运行及本机交付记录为准。未编译或未实测的新增内容不计入已通过实机验收。

补译构建42471704886已成功：x64 Release编译/链接、63项静态及2089项原生测试通过，2项GPU用例跳过，0失败。已单独安装并启动反馈副本，日志确认初始化和服务器列表接收；两条新增译文的游戏内显示仍等待用户确认。源码提交f2aac16，基础包c9b7405保持不变。
