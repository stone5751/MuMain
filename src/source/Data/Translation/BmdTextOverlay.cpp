#include "Data/Translation/BmdTextOverlay.h"
#include "Core/Utilities/StringUtils.h"
#include "json.hpp"

#include <array>
#include <algorithm>
#include <regex>
#include <set>
#include <stdexcept>
#include <vector>

namespace Data::Translation
{
namespace
{
using Kind = BmdTextOverlay::Kind;
constexpr std::size_t MaximumEntries = 4096;
constexpr std::size_t MaximumJsonBytes = 2 * 1024 * 1024;
constexpr int SkillCount = 650;
constexpr int QuestCount = 200;
constexpr int MaximumWordsId = 1000000;
constexpr int SlideCount = 5 * BmdTextOverlay::SlideSlotsPerLevel;
// QuestWords also supplies list subjects in 64-wide-character buffers. Reserve
// space for the numbered prefix, even when a future entry is used as a subject.
// Dialogue-only accessors wrap into 35 rows; never use this larger limit for
// list subjects or answers that share the original QuestWords table.
constexpr std::array<std::size_t, 6> TextLimits = {49, 31, 50, 255, 200, 200};

Kind ParseKind(const std::string& name)
{
    if (name == "skills")
        return Kind::Skill;
    if (name == "quest-titles")
        return Kind::QuestTitle;
    if (name == "quest-words")
        return Kind::QuestWords;
    if (name == "slides")
        return Kind::Slide;
    if (name == "quest-dialogue")
        return Kind::QuestDialogue;
    if (name == "quest-summary")
        return Kind::QuestSummary;
    throw std::runtime_error("Unknown BMD text kind");
}

int ReadId(const nlohmann::json& value, Kind kind)
{
    constexpr std::array<int, 6> limits = {SkillCount, QuestCount,     MaximumWordsId,
                                           SlideCount, MaximumWordsId, MaximumWordsId};
    if (!value.is_number_integer() || value < 0 || value >= limits[static_cast<std::size_t>(kind)])
        throw std::runtime_error("Invalid BMD text ID");
    return value.get<int>();
}

std::wstring ReadText(const nlohmann::json& value)
{
    const auto utf8 = value.get<std::string>();
    if (utf8.empty() || utf8.find('\0') != std::string::npos)
        throw std::runtime_error("Empty text or embedded NUL");
    const auto wide = StringUtils::NarrowToWide(utf8);
    if (StringUtils::WideToNarrow(wide.c_str()) != utf8)
        throw std::runtime_error("Invalid UTF-8 text");
    return wide;
}

std::size_t Utf16Length(std::wstring_view text)
{
    std::size_t length = 0;
    for (const auto ch : text)
        length += static_cast<unsigned int>(ch) > 0xffff ? 2 : 1;
    return length;
}

std::vector<std::wstring> TextTokens(const std::wstring& text)
{
    static const std::wregex tokens(
        LR"(%(?:%|(?:[0-9]+\$)?[-+ #0]*(?:[0-9]+|\*)?(?:\.(?:[0-9]+|\*))?(?:I64|I32|hh|ll|[hlLjztI])?[diuoxXfFeEgGaAcCsSpn])|\{[^{}]*\}|[{}%;\r\n\t])");
    std::vector<std::wstring> result;
    for (std::wsregex_iterator it(text.begin(), text.end(), tokens), end; it != end; ++it)
        result.push_back(it->str());
    return result;
}

void ValidateText(Kind kind, const std::wstring& english, const std::wstring& chinese)
{
    if (Utf16Length(chinese) > TextLimits[static_cast<std::size_t>(kind)])
        throw std::runtime_error("BMD overlay text exceeds display capacity");
    for (const auto ch : chinese)
        if ((ch < L' ' && ch != L'\r' && ch != L'\n' && ch != L'\t') || ch == 0x7f || ch == 0xfffd)
            throw std::runtime_error("Unsupported control character");
    if (TextTokens(english) != TextTokens(chinese))
        throw std::runtime_error("Placeholder or paragraph separator mismatch");
    if (std::count(english.begin(), english.end(), L'%') != std::count(chinese.begin(), chinese.end(), L'%'))
        throw std::runtime_error("Percent token mismatch");
}

nlohmann::json ReadDocument(std::istream& input)
{
    std::string bytes;
    char ch;
    while (input.get(ch))
    {
        if (bytes.size() >= MaximumJsonBytes)
            throw std::runtime_error("Overlay file too large");
        bytes.push_back(ch);
    }
    std::vector<std::set<std::string>> keys;
    auto uniqueKeys = [&keys](int, nlohmann::json::parse_event_t event, nlohmann::json& parsed)
    {
        if (event == nlohmann::json::parse_event_t::object_start)
            keys.emplace_back();
        if (event == nlohmann::json::parse_event_t::object_end)
            keys.pop_back();
        if (event == nlohmann::json::parse_event_t::key && !keys.back().insert(parsed.get<std::string>()).second)
            throw std::runtime_error("Duplicate JSON member");
        return true;
    };
    return nlohmann::json::parse(bytes, uniqueKeys);
}
} // namespace

bool BmdTextOverlay::Load(std::istream& input, std::string& error)
{
    m_entries.clear();
    error.clear();
    try
    {
        const auto document = ReadDocument(input);
        if (document.at("formatVersion") != 1 || document.at("locale") != "zh-CN")
            throw std::runtime_error("Unsupported BMD overlay format or locale");
        const auto& entries = document.at("entries");
        if (!entries.is_array() || entries.size() > MaximumEntries)
            throw std::runtime_error("Invalid overlay entries");
        for (const auto& row : entries)
        {
            const auto kind = ParseKind(row.at("kind").get<std::string>());
            const auto id = ReadId(row.at("id"), kind);
            if (kind == Kind::QuestWords || kind == Kind::QuestDialogue || kind == Kind::QuestSummary)
            {
                for (const auto other : {Kind::QuestWords, Kind::QuestDialogue, Kind::QuestSummary})
                    if (m_entries.contains({other, id}))
                        throw std::runtime_error("Duplicate QuestWords ID across display roles");
            }
            Entry entry{ReadText(row.at("english")), ReadText(row.at("zh-CN"))};
            ValidateText(kind, entry.english, entry.chinese);
            if (!m_entries.emplace(std::make_pair(kind, id), std::move(entry)).second)
                throw std::runtime_error("Duplicate BMD text ID");
        }
        return true;
    }
    catch (const std::exception& exception)
    {
        m_entries.clear();
        error = exception.what();
        return false;
    }
}

const wchar_t* BmdTextOverlay::Resolve(Kind kind, int id, const wchar_t* original, std::string_view locale) const
{
    if (locale != "zh-CN" || original == nullptr)
        return original;
    const auto it = m_entries.find({kind, id});
    if (it == m_entries.end() || it->second.english != original)
        return original;
    return it->second.chinese.c_str();
}

BmdTextOverlay& BmdTextOverlay::Instance()
{
    static BmdTextOverlay overlay;
    return overlay;
}
} // namespace Data::Translation
