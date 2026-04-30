#pragma once

#include <string>
#include <nlohmann/json.hpp>

class AnalysisService {
public:

    static nlohmann::json analyze(
        const std::string& calc_path,
        const std::string& ref_path,
        const std::string& clk_path
    );

}; 