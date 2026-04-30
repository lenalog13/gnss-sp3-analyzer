#include "clk_parser.h"

#include <QFile>
#include <QTextStream>

bool ClkParser::parse(const QString& path, CLK_MAP& out)
{
    QFile file(path);

    if (!file.open(QIODevice::ReadOnly))
        return false;

    QTextStream in(&file);

    while (!in.atEnd()) {
        QString line = in.readLine();

        if (!line.startsWith("AS"))
            continue;

        QStringList parts = line.split(" ", Qt::SkipEmptyParts);

        if (parts.size() < 10)
            continue;

        QString sat_str = parts[1];

        int year   = parts[2].toInt();
        int month  = parts[3].toInt();
        int day    = parts[4].toInt();
        int hour   = parts[5].toInt();
        int minute = parts[6].toInt();
        double sec = parts[7].toDouble();

        double clk = parts[9].toDouble();

        QDateTime dt(QDate(year, month, day),
                     QTime(hour, minute, (int)sec));

        Satellite sat = Satellite::fromString(sat_str);

        out[{dt, sat}] = clk;
    }

    return true;
}