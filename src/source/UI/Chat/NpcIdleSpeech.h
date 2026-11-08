#pragma once

#include <array>
#include <string_view>

namespace UI::Chat
{
// One cache per character balloon. Only automatic NPC idle speech may consult
// it; ordinary chat clears it and always follows the existing message path.
class NpcIdleSpeech
{
public:
    bool IsVisibleRepeat(std::wstring_view text, bool visible) const;
    void Remember(std::wstring_view text);
    void Clear();

private:
    static constexpr std::size_t Capacity = 256;
    std::array<wchar_t, Capacity> m_text{};
    std::size_t m_length = 0;
};
} // namespace UI::Chat
