#include "analysis_service.h"
#include <nlohmann/json.hpp>

using json = nlohmann::json;

json AnalysisService::analyze(const std::string& calcPath,
                             const std::string& refPath)
{
    json result;
    result["epochs"] = json::array();

    for (int i = 0; i < 50; i++) {
        result["epochs"].push_back({
            {"t", i},
            {"dx", sin(i * 0.1)},
            {"dy", cos(i * 0.1)},
            {"dz", sin(i * 0.2)},
            {"dr", 0.0},
            {"dt", 0.0},
            {"dn", 0.0},
            {"clk", 0.0}
        });
    }

    return result;
}