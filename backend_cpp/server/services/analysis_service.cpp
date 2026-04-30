#include "analysis_service.h"
#include "../services/clk_parser.h"

#include <QFile>
#include <QString>
#include <cmath>

#include <Sp3/reader.h>

using namespace sp3;

nlohmann::json AnalysisService::analyze(
    const std::string& calc_path,
    const std::string& ref_path,
    const std::string& clk_path)
{
    SP3_FILE calc_sp3;
    SP3_FILE ref_sp3;
    CLK_MAP clk_data;

    // ===== CLK (опционально) =====
    if (!clk_path.empty()) {
        ClkParser::parse(QString::fromStdString(clk_path), clk_data);
    }

    // ===== SP3 =====
    QFile calcFile(QString::fromStdString(calc_path));
    QFile refFile(QString::fromStdString(ref_path));

    bool ok1 = Sp3Reader::parse(calcFile, calc_sp3);
    bool ok2 = Sp3Reader::parse(refFile, ref_sp3);

    if (!ok1) {
        return {{"error", "calc parse failed"}};
    }

    if (!ok2) {
        return {{"error", "ref parse failed"}};
    }

    nlohmann::json result;
    result["epochs"] = nlohmann::json::array();

    // ===== ОСНОВНОЙ ЦИКЛ =====
    for (auto it = calc_sp3.records.begin(); it != calc_sp3.records.end(); ++it)
    {
        const QDateTime& epoch = it.key();

        // 🔥 ищем ближайшую эпоху в ref
        auto it_ref = ref_sp3.records.lowerBound(epoch);

        if (it_ref == ref_sp3.records.end())
            continue;

        QDateTime ref_epoch = it_ref.key();

        // ограничение по времени (например 15 минут)
        qint64 dt = std::abs(ref_epoch.secsTo(epoch));
        if (dt > 900)
            continue;

        const auto& sats     = it.value();
        const auto& ref_sats = it_ref.value();

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

            // ===== CLOCK =====
            double clk = NAN;

            if (!clk_path.empty()) {
                ClkKey key{epoch, sat};

                if (clk_data.contains(key)) {
                    clk = clk_data[key];
                }
            }

            result["epochs"].push_back({
                {"t", epoch.toSecsSinceEpoch()},
                {"dx", dx},
                {"dy", dy},
                {"dz", dz},
                {"clk", clk}
            });
        }
    }

    // Просто выводим количество по аналогии с оригинальным кодом
        std::cout << "calc: " << calc_sp3.records.size() << " эпох" << std::endl;

        int total_sats = 0;
        for (auto it = calc_sp3.records.begin(); it != calc_sp3.records.end(); ++it) {
            total_sats += it.value().size();
        }
        std::cout << "Всего записей о спутниках: " << total_sats << std::endl;

        // Статистика для ref
    int ref_epoch_count = ref_sp3.records.size();
    int ref_sat_count = 0;
    for (auto it = ref_sp3.records.begin(); it != ref_sp3.records.end(); ++it) {
        ref_sat_count += it.value().size();
    }
    std::cout << "ref: " << ref_epoch_count << " эпох, " << ref_sat_count << " записей о спутниках" << std::endl;

    return result;
}