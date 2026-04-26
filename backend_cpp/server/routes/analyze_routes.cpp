#include "analyze_routes.h"
#include "../services/analysis_service.h"

void register_analyze_routes(crow::SimpleApp& app) {

    CROW_ROUTE(app, "/analyze").methods("POST"_method)
    ([](const crow::request& req) {

        AnalysisService service;
        auto data = service.runFakeAnalysis();

        crow::json::wvalue res;

        for (int i = 0; i < data.size(); i++) {
            res["epochs"][i]["t"] = data[i].t;
            res["epochs"][i]["dx"] = data[i].dx;
            res["epochs"][i]["dy"] = data[i].dy;
            res["epochs"][i]["dz"] = data[i].dz;
        }

        res["experiment_id"] = 1;

        return res;  
    });

}