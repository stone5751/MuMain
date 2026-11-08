# 剩余翻译与术语复核

完整待翻译资源键在 `current/missing-resources.tsv`；名称、数字 ID、源文件和现有译文在 `current/names.tsv`（zh-CN 空列即缺失）。不要根据名称顺序重新编号。

## 保留原文的范围

- Game 仍有 2398 个缺失键，涉及大量活动、特殊道具、进阶系统及其他未覆盖界面；没有用机翻填满。
- Editor 1417 项、Metadata 59 项尚未翻译，玩家无编辑器构建优先。
- 物品 456 组、怪物 122 组、NPC 44 组仍无中文；包括版本差异明显的后期装备、套装、专名及历史空白占位。完整清单以 TSV 为准。
- `Divine Stick of the Archangel` 未确认对应的大陆名称，本轮撤回试译并保留英文，避免与大天使法杖等装备混淆。
- Dialog 对话中的 Muren、Sekneum、Lunedil、Etramu、Arka、Semeden、Elbe、Apocalypse、Benelope、Gaion、Secromicon、Lugard、Eresia、Baz 等未确认专名保留原文。翻译句子不等于这些名称已审核。
- 玩家名、队名、服务端动态消息、技术命令、文件名、协议标识不做自动翻译。

## 经典术语依据

优先依据大陆官方资料核对地图/NPC、转职材料与技能用语；保留 v1.37.0 英文源文本的等级、数量等要求，不用较新官网数值覆盖旧客户端数据。

- [官方转职任务](https://mu.zhaouc.com/Guide/GameSystem/08_quest.html)：任务人物及材料用语。
- [官方大陆地图/NPC](https://mu.zhaouc.com/Guide/GameIntro/02_area01.html)：勇者大陆等经典地名/NPC；同系列地图页面辅助核对。
- [官方职业资料](https://mu.zhaouc.com/news/Update/212.html)：职业、进阶职业用语。
- [官方芬里尔资料](https://mu.zhaouc.com/01_news/updatecn/fourthupdate/other_update.htm)：破烂的铠甲、女神的祝福、猛兽的脚甲、碎角片、折断的角等材料。
- [官方大师技能说明](https://mu.zhaouc.com/Guide/GameSystem/09_master.html)：技能中文表达参照。
- [MU 数据资料的真空波术条目](https://mu.dvg.cn/item_info.php?id=4672)：辅助核对 Group 15 / Number 10，Scroll of Power Wave 不译为能量球；仅用作术语参考，未采用其数值。

常用词统一为奇迹助手、背包、仓库、战盟、祝福宝石、灵魂宝石、玛雅之石、霹雳回旋斩、圣盾防御、天地十字剑等。物品组映射与全部新增译文仍需要熟悉本服版本的玩家做最终语义验收；格式校验不能证明译名对应关系正确。

## 独立 BMD 文本

`legacy-bmd/` 为原安装包 English BMD 的只读提取结果，不是新语言文件。包含 399 条非空技能名、7 条任务标题、2288 条任务正文记录；原始 SHA-256 和编码异常 ID 在 `summary.json`。
部分任务正文不能按 UTF-8 严格解码，清单以转义字节保留并标记，未擅自替换原文件。
应单独设计按稳定 ID 的语言覆盖层，或先确认 BMD 布局、编码和载入路径再制作中文文本。当前不得把它们复制回 Data 当成可用 BMD。
大师技能说明、地图标题图片、服务端直接发送的文案也不由这次 resx/JSON 修改覆盖。

## 硬编码清单的解读

`baseline/wide-literal-candidates.tsv` 和 `supplemental/{narrow-display-candidates,rml-text-candidates}.tsv` 是候选，不是确认漏翻数。补充扫描包括编辑器/第三方源码；RML `<title>` 常是内部文档名，ImGui `##...` 常是控件 ID，必须先判定是否可见。
当前补充扫描记录 14286 个窄字面量候选，其中 405 个处于显示相关调用行；RML 文本候选 248 个。正则不能完整解析跨行文本、宏、注释和动态数据。
已改结果弹窗 OK；连接失败/渲染器错误等早期错误提示、幸运物品兑换韩文标题仍待处理。后者所属功能原项目尚未完成，避免为翻译扩大业务改动。
