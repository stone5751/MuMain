#pragma once

#include <istream>
#include <map>
#include <string>
#include <string_view>

namespace Data::Translation
{
class BmdTextOverlay
{
public:
    enum class Kind
    {
        Skill,
        QuestTitle,
        QuestWords,
        Slide,
        QuestDialogue
    };
    static constexpr int SlideSlotsPerLevel = 32;
    static constexpr const char* FilePath = "Data/Local/BmdText.zh-CN.json";

    // Load only at startup; returned text pointers live until the next Load.
    bool Load(std::istream& input, std::string& error);
    const wchar_t* Resolve(Kind kind, int id, const wchar_t* original, std::string_view locale) const;
    std::size_t Size() const
    {
        return m_entries.size();
    }
    static BmdTextOverlay& Instance();

private:
    struct Entry
    {
        std::wstring english;
        std::wstring chinese;
    };
    std::map<std::pair<Kind, int>, Entry> m_entries;
};

// Display-only access. Does not mutate the English BMD tables or read files.
const wchar_t* BmdDisplayText(BmdTextOverlay::Kind kind, int id, const wchar_t* original);
void LoadBmdTextOverlay();
} // namespace Data::Translation
