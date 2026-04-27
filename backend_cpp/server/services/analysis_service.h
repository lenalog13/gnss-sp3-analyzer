#pragma once
#include <vector>

struct Epoch {
    double t;

    double dx, dy, dz;   // ECEF
    double dR, dT, dN;   // RTN
};

class AnalysisService {
public:
    std::vector<Epoch> runFakeAnalysis();
};