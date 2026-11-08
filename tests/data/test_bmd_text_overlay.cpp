#include "stdafx.h"
#include "doctest.h"
#include "Data/Translation/BmdTextOverlay.h"
#include "GameLogic/Skills/SkillManager.h"
#include "I18N/All.h"
#include "json.hpp"
#include <fstream>
#include <sstream>

using Data::Translation::BmdTextOverlay;
using Kind = BmdTextOverlay::Kind;

namespace
{
nlohmann::json Sample()
{
    return {{"formatVersion", 1},
            {"locale", "zh-CN"},
            {"entries",
             nlohmann::json::array({{{"kind", "skills"}, {"id", 4}, {"english", "Fire Ball"}, {"zh-CN", "火球术"}}})}};
}

bool Load(BmdTextOverlay& overlay, const nlohmann::json& json)
{
    std::istringstream input(json.dump());
    std::string error;
    return overlay.Load(input, error);
}
} // namespace

TEST_CASE("BMD overlay resolves only the guarded ID and Chinese locale [data][i18n]")
{
    BmdTextOverlay overlay;
    REQUIRE(Load(overlay, Sample()));
    CHECK(std::wstring(overlay.Resolve(Kind::Skill, 4, L"Fire Ball", "zh-CN")) == L"火球术");
    for (const auto* locale : {"en", "de", "zh-TW", ""})
        CHECK(std::wstring(overlay.Resolve(Kind::Skill, 4, L"Fire Ball", locale)) == L"Fire Ball");
    CHECK(std::wstring(overlay.Resolve(Kind::Skill, 3, L"Fire Ball", "zh-CN")) == L"Fire Ball");
    CHECK(std::wstring(overlay.Resolve(Kind::QuestWords, 4, L"Fire Ball", "zh-CN")) == L"Fire Ball");
    CHECK(std::wstring(overlay.Resolve(Kind::Skill, 4, L"Changed source", "zh-CN")) == L"Changed source");
    CHECK(overlay.Resolve(Kind::Skill, 4, nullptr, "zh-CN") == nullptr);
}

TEST_CASE("BMD overlay rejects invalid documents atomically [data][i18n]")
{
    BmdTextOverlay overlay;
    auto document = Sample();
    SUBCASE("duplicate ID")
    {
        document["entries"].push_back(document["entries"][0]);
    }
    SUBCASE("negative ID")
    {
        document["entries"][0]["id"] = -1;
    }
    SUBCASE("out of range ID")
    {
        document["entries"][0]["id"] = 650;
    }
    SUBCASE("fractional ID")
    {
        document["entries"][0]["id"] = 4.5;
    }
    SUBCASE("huge ID")
    {
        document["entries"][0]["id"] = 18446744073709551615ULL;
    }
    SUBCASE("missing ID")
    {
        document["entries"][0].erase("id");
    }
    SUBCASE("unknown kind")
    {
        document["entries"][0]["kind"] = "attributes";
    }
    SUBCASE("wrong locale")
    {
        document["locale"] = "en";
    }
    SUBCASE("wrong version")
    {
        document["formatVersion"] = 2;
    }
    SUBCASE("long name")
    {
        document["entries"][0]["zh-CN"] = std::string(50, 'a');
    }
    SUBCASE("empty text")
    {
        document["entries"][0]["zh-CN"] = "";
    }
    SUBCASE("embedded NUL")
    {
        document["entries"][0]["zh-CN"] = std::string("a\0b", 3);
    }
    SUBCASE("control character")
    {
        document["entries"][0]["zh-CN"] = "a\x01";
    }
    SUBCASE("paragraph mismatch")
    {
        document["entries"][0]["zh-CN"] = "a;b";
    }
    SUBCASE("placeholder mismatch")
    {
        document["entries"][0]["zh-CN"] = "%ls";
    }
    REQUIRE(Load(overlay, Sample()));
    CHECK_FALSE(Load(overlay, document));
    CHECK(overlay.Size() == 0);
    CHECK(std::wstring(overlay.Resolve(Kind::Skill, 4, L"Fire Ball", "zh-CN")) == L"Fire Ball");
}

TEST_CASE("BMD overlay rejects malformed UTF8 and duplicate JSON members [data][i18n]")
{
    for (const auto& bytes : {std::string("{bad"), std::string(""),
                              std::string(R"({"formatVersion":1,"formatVersion":1,"locale":"zh-CN","entries":[]})"),
                              std::string("{\"formatVersion\":1,\"locale\":\"zh-CN\",\"entries\":[{\"kind\":\"skills\","
                                          "\"id\":4,\"english\":\"Fire Ball\",\"zh-CN\":\"\xff\"}]}")})
    {
        BmdTextOverlay overlay;
        std::istringstream input(bytes);
        std::string error;
        CHECK_FALSE(overlay.Load(input, error));
        CHECK_FALSE(error.empty());
        CHECK(overlay.Size() == 0);
    }
}

TEST_CASE("BMD overlay preserves formatting and paragraph tokens [data][i18n]")
{
    auto document = Sample();
    auto& row = document["entries"][0];
    row["kind"] = "quest-words";
    row["english"] = "Hello %ls;value %d\r\n{0}\t100%%";
    row["zh-CN"] = "你好 %ls;数值 %d\r\n{0}\t100%%";
    BmdTextOverlay overlay;
    CHECK(Load(overlay, document));
    row["zh-CN"] = "你好 %d;数值 %ls\r\n{0}\t100%%";
    CHECK_FALSE(Load(overlay, document));
}

TEST_CASE("BMD overlay limits each display buffer in UTF16 units [data][i18n]")
{
    for (const auto& [kind, capacity] : std::vector<std::pair<std::string, std::size_t>>{
             {"skills", 49}, {"quest-titles", 31}, {"quest-words", 50}, {"slides", 255}})
    {
        BmdTextOverlay overlay;
        auto document = Sample();
        document["entries"][0]["kind"] = kind;
        document["entries"][0]["zh-CN"] = std::string(capacity, 'a');
        CHECK(Load(overlay, document));
        document["entries"][0]["zh-CN"] = std::string(capacity + 1, 'a');
        CHECK_FALSE(Load(overlay, document));
    }
    auto document = Sample();
    document["entries"][0]["zh-CN"] = std::string(48, 'a') + "\xf0\x9f\x98\x80";
    BmdTextOverlay overlay;
    CHECK_FALSE(Load(overlay, document));
}

TEST_CASE("BMD overlay ships the reviewed MVP samples [data][i18n]")
{
    std::ifstream file(MU_TEST_DATA_DIR "/Local/BmdText.zh-CN.json");
    BmdTextOverlay overlay;
    std::string error;
    REQUIRE(overlay.Load(file, error));
    CHECK(overlay.Size() == 68);
    CHECK(std::wstring(overlay.Resolve(Kind::Slide, 12, L"Press space bar to collect loot.", "zh-CN")) ==
          L"按空格键拾取物品。");
    CHECK(std::wstring(overlay.Resolve(Kind::QuestTitle, 0, L"Find the 'Scroll of Emperor'!", "zh-CN")) ==
          L"寻找帝王之书");
    CHECK(std::wstring(overlay.Resolve(Kind::QuestWords, 2, L"Continue listening.", "zh-CN")) == L"继续听下去。");
}

TEST_CASE("BMD skill accessor switches language without mutating attributes [data][i18n]")
{
    const std::string previousLocale = I18N::GetCurrentLocale();
    const auto previous = SkillAttribute;
    std::vector<SKILL_ATTRIBUTE> skills(MAX_SKILLS);
    wcscpy(skills[4].Name, L"Fire Ball");
    skills[4].Mana = 17;
    skills[4].Distance = 6;
    std::array<unsigned char, sizeof(SKILL_ATTRIBUTE)> original{};
    std::memcpy(original.data(), &skills[4], original.size());
    SkillAttribute = skills.data();
    auto& overlay = BmdTextOverlay::Instance();
    const bool loaded = Load(overlay, Sample());
    CHECK(loaded);
    for (const auto* locale : {"zh-CN", "en", "zh-CN", "en"})
    {
        I18N::SetLocale(locale);
        wchar_t name[50]{};
        int mana = 0, distance = 0;
        gSkillManager.GetSkillInformation(4, 1, name, &mana, &distance);
        CHECK(std::wstring(name) == (std::string_view(locale) == "zh-CN" ? L"火球术" : L"Fire Ball"));
        CHECK(mana == 17);
        CHECK(distance == 6);
        CHECK(std::memcmp(&skills[4], original.data(), original.size()) == 0);
    }
    SkillAttribute = previous;
    I18N::SetLocale(previousLocale.c_str());
    std::istringstream empty;
    std::string error;
    overlay.Load(empty, error);
}
