#include "stdafx.h"
#include "Data/Translation/BmdTextOverlay.h"
#include "Core/Utilities/StringUtils.h"
#include "I18N/All.h"
#include <fstream>

namespace Data::Translation
{
const wchar_t* BmdDisplayText(BmdTextOverlay::Kind kind, int id, const wchar_t* original)
{
    return BmdTextOverlay::Instance().Resolve(kind, id, original, I18N::GetCurrentLocale());
}

void LoadBmdTextOverlay()
{
    std::ifstream input(BmdTextOverlay::FilePath, std::ios::binary);
    std::string error;
    if (!BmdTextOverlay::Instance().Load(input, error))
    {
        const auto message =
            StringUtils::NarrowToWide("BMD text overlay unavailable; original text retained: " + error + "\r\n");
        g_ErrorReport.Write(message.c_str());
        return;
    }
    g_ErrorReport.Write(L"BMD zh-CN text overlay loaded; English source tables retained.\r\n");
}
} // namespace Data::Translation
