#pragma once
#include <vector>

struct Epoch {
    double t;
    double dx;
    double dy;
    double dz;   
};

class AnalysisService {
public:
    std::vector<Epoch> runFakeAnalysis();
};