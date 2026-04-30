#pragma once

#include <QMap>
#include <QDateTime>
#include <QString>

#include <inav/Satellite>

struct ClkKey {
    QDateTime dt;
    Satellite sat;

    bool operator<(const ClkKey& other) const {
        return std::tie(dt, sat) < std::tie(other.dt, other.sat);
    }
};

using CLK_MAP = QMap<ClkKey, double>;

class ClkParser {
public:
    static bool parse(const QString& path, CLK_MAP& out);
};