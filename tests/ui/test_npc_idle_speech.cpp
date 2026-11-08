#include <doctest.h>
#include "UI/Chat/NpcIdleSpeech.h"
#include <string>

TEST_CASE("NPC idle speech suppresses only the same currently visible line [ui][chat]")
{
    UI::Chat::NpcIdleSpeech first, second;
    const auto* line = L"我会助你成长为一名勇士。";
    CHECK_FALSE(first.IsVisibleRepeat(line, true));
    first.Remember(line);
    CHECK(first.IsVisibleRepeat(line, true));
    CHECK_FALSE(first.IsVisibleRepeat(line, false));
    CHECK_FALSE(second.IsVisibleRepeat(line, true));
    CHECK_FALSE(first.IsVisibleRepeat(L"欢迎来到勇者大陆。", true));
    first.Remember(L"欢迎来到勇者大陆。");
    CHECK_FALSE(first.IsVisibleRepeat(line, true));
}

TEST_CASE("ordinary messages invalidate automatic NPC speech history [ui][chat]")
{
    UI::Chat::NpcIdleSpeech speech;
    speech.Remember(L"A");
    speech.Clear(); // AddChat does this for every ordinary/player/server message.
    CHECK_FALSE(speech.IsVisibleRepeat(L"A", true));
    speech.Remember(L"B");
    CHECK_FALSE(speech.IsVisibleRepeat(L"A", true));
    CHECK(speech.IsVisibleRepeat(L"B", true));
}

TEST_CASE("NPC idle speech compares complete text across wrapping and locale changes [ui][chat]")
{
    UI::Chat::NpcIdleSpeech speech;
    const auto english = L"I'll be your strength for the journey to become a warrior.";
    speech.Remember(english);
    CHECK(speech.IsVisibleRepeat(english, true));
    CHECK_FALSE(speech.IsVisibleRepeat(L"我会助你成长为一名勇士。", true));
    CHECK_FALSE(speech.IsVisibleRepeat(L"journey to become a warrior.", true));
    speech.Remember(std::wstring(256, L'x'));
    CHECK_FALSE(speech.IsVisibleRepeat(std::wstring(256, L'x'), true));
    speech.Remember(L"");
    CHECK_FALSE(speech.IsVisibleRepeat(L"", true));
}
