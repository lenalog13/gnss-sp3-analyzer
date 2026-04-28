#include "analysis_service.h"

#include <QFile>
#include <QString>

#include <Sp3/reader.h>

using namespace sp3;

nlohmann::json AnalysisService::analyze(
    const std::string& calc_path,
    const std::string& ref_path)
{
    SP3_FILE calc_sp3;
    SP3_FILE ref_sp3;

    bool ok1 = Sp3Reader::parse(
        QString::fromStdString(calc_path), "", calc_sp3);

    bool ok2 = Sp3Reader::parse(
        QString::fromStdString(ref_path), "", ref_sp3);

    if (!ok1) {
        return {{"error", "calc parse failed"}};
    }

    if (!ok2) {
        return {{"error", "ref parse failed"}};
    }

    nlohmann::json result;
    result["epochs"] = nlohmann::json::array();

    for (auto it = calc_sp3.records.begin(); it != calc_sp3.records.end(); ++it)
    {
        const QDateTime& epoch = it.key();
        const auto& sats = it.value();

        if (!ref_sp3.records.contains(epoch))
            continue;

        const auto& ref_sats = ref_sp3.records[epoch];

        for (auto sit = sats.begin(); sit != sats.end(); ++sit)
        {
            const Satellite& sat = sit.key();

            if (!ref_sats.contains(sat))
                continue;

            const auto& c = sit.value();
            const auto& r = ref_sats[sat];

            double dx = c.coord.x - r.coord.x;
            double dy = c.coord.y - r.coord.y;
            double dz = c.coord.z - r.coord.z;

            result["epochs"].push_back({
                {"t", epoch.toSecsSinceEpoch()},
                {"dx", dx},
                {"dy", dy},
                {"dz", dz}
            });
        }
    }

    return result;
}