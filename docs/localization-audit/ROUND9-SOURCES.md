# Round 9 translation provenance

All mappings apply to explicit client IDs and the original English text; web pages provide terminology, not executable data. No downloaded game assets are included.

- Existing `Game.zh-TW.resx` and `Game.en.resx`: draft and original placeholders; simplified conversion followed by manual corrections for party/guild, Zen, commands, mainland place names and UI wording. Existing Round 8 Chinese entries remain unchanged.
- Mainland official Rage Fighter introduction: https://mu.zhaouc.com/news/Update/212.html and https://mu.zhaouc.com/Guide/GameIntro/01_character07.html
- Mainland official master system and classic quests: https://mu.zhaouc.com/Guide/GameSystem/09_master.html and https://mu.zhaouc.com/guide/gamesystem/08_quest.html
- Official equipment terminology: https://mu.zhaouc.com/news/Notice/1221.html and https://mu.zhaouc.com/01_news/updatecn/newitem/newitem.htm
- DVG equipment records: `round9-item-source-facts.json` records individual page references. Armor family correspondence was cross-checked with group/number and international names, including https://mu.dvg.cn/items.php?iclass=0&p=81&type=0&zytype=2 and https://mu.dvg.cn/v2_item_list.php?category=armor&class=2&order=defense_asc&page=1&scope=all&variant=all&view=grid . Site page/database IDs are not client item IDs.
- Monster 304 Witch Queen / 丛林女巫师 and 312 Bow Scout / 魔弓侦察兵: https://mu.dvg.cn/monster_info.php?id=304 and https://mu.dvg.cn/monster_info.php?id=312 . Skill records for creature summons and ordinary active skills were checked by original skill ID (`skill_info.php?id=...`).

Names with literal descriptive translations are marked as such in manifests, not claimed as official mainland names. Uncertain proper-name/version correspondences remain in pending lists. Personal names such as Leo, Luke and Layla remain Latin when no verified mainland name was established. Modern skill descriptions must not be assumed identical to Season 6; six ambiguous original skill names remain English.

The manifests describe source edits, not successful in-game encounters. Local structure, placeholder, source-ID, original-BMD hash and font-cmap validation is separate from Actions compilation and manual gameplay acceptance.
