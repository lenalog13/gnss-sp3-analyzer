#include "analyze_routes.h"
#include "../services/analysis_service.h"
#include "crow.h"

void setupAnalyzeRoutes(crow::SimpleApp& app) {

    CROW_ROUTE(app, "/analyze").methods("POST"_method)
    ([]() {
        AnalysisService service;
        auto data = service.runFakeAnalysis();

        crow::json::wvalue res;

        for (int i = 0; i < data.size(); i++) {
            res["epochs"][i]["t"]  = data[i].t;

            res["epochs"][i]["dx"] = data[i].dx;
            res["epochs"][i]["dy"] = data[i].dy;
            res["epochs"][i]["dz"] = data[i].dz;

            res["epochs"][i]["dR"] = data[i].dR;
            res["epochs"][i]["dT"] = data[i].dT;
            res["epochs"][i]["dN"] = data[i].dN;
        }

        return res;
    });
}