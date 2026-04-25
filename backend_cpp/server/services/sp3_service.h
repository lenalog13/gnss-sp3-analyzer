#pragma once
#include <string>
#include <vector>

struct EpochData {
    double t;
    double dx, dy, dz;
};

class Sp3Service {
public:
    std::vector<EpochData> parse(const std::string& path);
};