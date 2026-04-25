#include "analyze_routes.h"
#include "../services/analysis_service.h"  // добавь это

void register_analyze_routes(crow::SimpleApp& app) {

    CROW_ROUTE(app, "/analyze").methods("POST"_method)
    ([](const crow::request& req) {

        AnalysisService service;
        auto data = service.runFakeAnalysis();

        crow::json::wvalue res;
        res["experiment_id"] = 1;

        for (int i = 0; i < data.size(); i++) {
            crow::json::wvalue epoch;

            epoch["t"]  = data[i].t;
            epoch["dx"] = data[i].dx;
            epoch["dy"] = data[i].dy;
            epoch["dz"] = data[i].dz;

            res["epochs"][i] = std::move(epoch);
        }
    });

}