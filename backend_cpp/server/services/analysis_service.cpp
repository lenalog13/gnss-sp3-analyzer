#include "analysis_service.h"
#include <cmath>

std::vector<Epoch> AnalysisService::runFakeAnalysis() {
    std::vector<Epoch> result;

    for (int i = 0; i < 100; i++) {
        Epoch e;
        e.t = i;
        e.dx = 0.1 * sin(i * 0.1);
        e.dy = 0.1 * cos(i * 0.1);
        e.dz = 0.05 * sin(i * 0.2);

        result.push_back(e);
    }

    return result;
}