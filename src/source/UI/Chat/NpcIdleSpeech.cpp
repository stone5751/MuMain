#include "UI/Chat/NpcIdleSpeech.h"

#include <algorithm>

namespace UI::Chat
{
bool NpcIdleSpeech::IsVisibleRepeat(std::wstring_view text, bool visible) const
{
    return visible && m_length != 0 && text == std::wstring_view(m_text.data(), m_length);
}

void NpcIdleSpeech::Remember(std::wstring_view text)
{
    Clear();
    if (text.empty() || text.size() >= Capacity)
        return; // Uncacheable text keeps the original display behavior.
    std::copy(text.begin(), text.end(), m_text.begin());
    m_length = text.size();
}

void NpcIdleSpeech::Clear()
{
    m_length = 0;
}
} // namespace UI::Chat
