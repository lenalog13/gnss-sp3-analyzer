#include "analysis_service.h"
#include <cmath>

struct Vec3 {
    double x, y, z;
};

static Vec3 operator-(const Vec3& a, const Vec3& b) {
    return {a.x - b.x, a.y - b.y, a.z - b.z};
}

static double dot(const Vec3& a, const Vec3& b) {
    return a.x*b.x + a.y*b.y + a.z*b.z;
}

static Vec3 cross(const Vec3& a, const Vec3& b) {
    return {
        a.y*b.z - a.z*b.y,
        a.z*b.x - a.x*b.z,
        a.x*b.y - a.y*b.x
    };
}

static Vec3 normalize(const Vec3& v) {
    double n = std::sqrt(dot(v,v));
    if (n == 0) return {0,0,0};
    return {v.x/n, v.y/n, v.z/n};
}

static void computeRTN(
    const Vec3& r,
    const Vec3& v,
    const Vec3& d,
    double& dR,
    double& dT,
    double& dN
) {
    Vec3 R = normalize(r);
    Vec3 N = normalize(cross(r, v));
    Vec3 T = cross(N, R);

    dR = dot(d, R);
    dT = dot(d, T);
    dN = dot(d, N);
}

std::vector<Epoch> AnalysisService::runFakeAnalysis() {
    std::vector<Epoch> result;

    for (int i = 1; i < 100; i++) {
        double t = i;

        double dx = std::sin(i * 0.1) * 0.1;
        double dy = std::cos(i * 0.1) * 0.1;
        double dz = std::sin(i * 0.1) * 0.05;

        Vec3 r = {
            static_cast<double>(10000 + i),
            static_cast<double>(20000 + i),
            static_cast<double>(30000 + i)
        };

        Vec3 r_next = {
            static_cast<double>(10000 + i + 1),
            static_cast<double>(20000 + i + 1),
            static_cast<double>(30000 + i + 1)
        };

        Vec3 v = r_next - r;
        Vec3 d = {dx, dy, dz};

        double dR, dT, dN;
        computeRTN(r, v, d, dR, dT, dN);

        Epoch e;
        e.t = t;
        e.dx = dx;
        e.dy = dy;
        e.dz = dz;

        e.dR = dR;
        e.dT = dT;
        e.dN = dN;

        result.push_back(e);
    }

    return result;
}