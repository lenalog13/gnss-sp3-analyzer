#pragma once
#include <string>
#include <nlohmann/json.hpp>

class AnalysisService {
public:
    static nlohmann::json analyze(const std::string& calcPath,
                                  const std::string& refPath);
};