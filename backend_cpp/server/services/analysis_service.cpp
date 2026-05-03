#include "analysis_service.h"
#include "../services/clk_parser.h"

#include <QFile>
#include <QString>
#include <QDebug>

#include <cmath>
#include <limits>
#include <iostream>

#include <Sp3/reader.h>

using namespace sp3;

struct Vec3 {
    double x, y, z;
};

static Vec3 operator-(const Vec3& a, const Vec3& b) {
    return {a.x - b.x, a.y - b.y, a.z - b.z};
}

static Vec3 cross(const Vec3& a, const Vec3& b) {
    return {
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x
    };
}

static double dot(const Vec3& a, const Vec3& b) {
    return a.x*b.x + a.y*b.y + a.z*b.z;
}

static double norm(const Vec3& v) {
    return std::sqrt(dot(v, v));
}

static Vec3 normalize(const Vec3& v) {
    double n = norm(v);
    if (n == 0) return {0,0,0};
    return {v.x/n, v.y/n, v.z/n};
}

// ================= CLOCK FIX из REF =================
static void fillMissingClockFromRef(SP3_FILE& calc,
                                    const SP3_FILE& ref)
{
    for (auto it = calc.records.begin(); it != calc.records.end(); ++it)
    {
        const QDateTime& epoch = it.key();

        if (!ref.records.contains(epoch))
            continue;

        auto& calcSats = it.value();
        const auto& refSats = ref.records[epoch];

        for (auto sit = calcSats.begin(); sit != calcSats.end(); ++sit)
        {
            const Satellite& sat = sit.key();

            if (!refSats.contains(sat))
                continue;

            auto& c = sit.value();
            const auto& r = refSats[sat];

            if (c.clock >= 999999.0 || std::isnan(c.clock))
            {
                c.clock = r.clock;
            }
        }
    }
}

// ================= MAIN =================
nlohmann::json AnalysisService::analyze(
    const std::string& calc_path,
    const std::string& ref_path,
    const std::string& clk_path)
{
    SP3_FILE calc_sp3;
    SP3_FILE ref_sp3;
    CLK_MAP clk_data;

    // ===== CLK =====
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

    fillMissingClockFromRef(calc_sp3, ref_sp3);

    nlohmann::json result;
    result["epochs"] = nlohmann::json::array();

    // ===== ОСНОВНОЙ ЦИКЛ =====
    for (auto it = calc_sp3.records.begin(); it != calc_sp3.records.end(); ++it)
    {
        const QDateTime& epoch = it.key();

        auto it_ref = ref_sp3.records.lowerBound(epoch);
        if (it_ref == ref_sp3.records.end())
            continue;

        QDateTime ref_epoch = it_ref.key();

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

            // ===== KEY =====
            ClkKey key{epoch, sat};

            // ===== CLOCK ЛОГИКА =====
            double clk = 0.0;

            // 1. из CLK файла
            if (!clk_path.empty() && clk_data.contains(key)) {
                clk = clk_data[key];
            }
            // 2. иначе из SP3
            else if (!std::isnan(c.clock) && c.clock < 999999.0) {
                clk = c.clock;
            }

            Vec3 r_vec = {r.coord.x, r.coord.y, r.coord.z};
            Vec3 eR = normalize(r_vec);

            // --- velocity через соседние эпохи ---
            Vec3 v_vec = {0,0,0};

            auto it_prev = (it == calc_sp3.records.begin()) ? it : std::prev(it);
            auto it_next = std::next(it);

            if (it_prev != calc_sp3.records.end() && it_next != calc_sp3.records.end()) {

                if (ref_sp3.records.contains(it_prev.key()) &&
                    ref_sp3.records.contains(it_next.key()))
                {
                    const auto& prev_sat = ref_sp3.records[it_prev.key()];
                    const auto& next_sat = ref_sp3.records[it_next.key()];

                    if (prev_sat.contains(sat) && next_sat.contains(sat)) {

                        Vec3 r_prev = {
                            prev_sat[sat].coord.x,
                            prev_sat[sat].coord.y,
                            prev_sat[sat].coord.z
                        };

                        Vec3 r_next = {
                            next_sat[sat].coord.x,
                            next_sat[sat].coord.y,
                            next_sat[sat].coord.z
                        };

                        v_vec = r_next - r_prev;
                    }
                }
            }

            Vec3 eT = normalize(v_vec);
            Vec3 eN = normalize(cross(eR, eT));

            Vec3 d = {dx, dy, dz};

            double dR = dot(d, eR);
            double dT = dot(d, eT);
            double dN = dot(d, eN);

            result["epochs"].push_back({
                {"t", epoch.toSecsSinceEpoch()},
                {"sat", sat.toString().toStdString()},
                {"dx", dx},
                {"dy", dy},
                {"dz", dz},
                {"dr", dR},
                {"dt", dT},
                {"dn", dN},
                {"clk", clk}
            });
        }
    }

    // ===== DEBUG =====
    qDebug() << "calc epochs:" << calc_sp3.records.size();
    qDebug() << "ref epochs:" << ref_sp3.records.size();

    // ===== STATISTICS =====
    double sum_x2 = 0, sum_y2 = 0, sum_z2 = 0;
    double sum_r2=0, sum_t2=0, sum_n2=0;
    double sum_clk2 = 0;

    double sum_x = 0;
    double max_x = 0;

    int count = 0;
    int clk_count = 0;

    for (const auto& e : result["epochs"])
    {
        double dx = e["dx"].get<double>();
        double dy = e["dy"].get<double>();
        double dz = e["dz"].get<double>();

        sum_x2 += dx * dx;
        sum_y2 += dy * dy;
        sum_z2 += dz * dz;

        double dr = e["dr"].get<double>();
        double dt = e["dt"].get<double>();
        double dn = e["dn"].get<double>();

        sum_r2 += dr*dr;
        sum_t2 += dt*dt;
        sum_n2 += dn*dn;

        sum_x += dx;
        max_x = std::max(max_x, std::abs(dx));

        count++;

        if (!e["clk"].is_null()) {
            double clk = e["clk"].get<double>();
            sum_clk2 += clk * clk;
            clk_count++;
        }
    }

    double rms_x = count ? std::sqrt(sum_x2 / count) : 0;
    double rms_y = count ? std::sqrt(sum_y2 / count) : 0;
    double rms_z = count ? std::sqrt(sum_z2 / count) : 0;

    double rms_r = count ? std::sqrt(sum_r2 / count) : 0;
    double rms_t = count ? std::sqrt(sum_t2 / count) : 0;
    double rms_n = count ? std::sqrt(sum_n2 / count) : 0;

    double rms_3d = std::sqrt(rms_x*rms_x + rms_y*rms_y + rms_z*rms_z);

    double mean = count ? sum_x / count : 0;
    double clock_rms = clk_count ? std::sqrt(sum_clk2 / clk_count) : 0;

    result["statistics"] = {
        {"rms_x", rms_x},
        {"rms_y", rms_y},
        {"rms_z", rms_z},
        {"rms_r", rms_r},
        {"rms_t", rms_t},
        {"rms_n", rms_n},
        {"rms_3d", rms_3d},
        {"mean", mean},
        {"max", max_x},
        {"clock_rms", clock_rms}
    };

    return result;
}