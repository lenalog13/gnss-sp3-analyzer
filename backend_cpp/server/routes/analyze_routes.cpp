#include "analyze_routes.h"

void register_analyze_routes(crow::SimpleApp& app) {

    CROW_ROUTE(app, "/analyze").methods("POST"_method)
    ([](const crow::request& req) {

        crow::json::wvalue res;

        res["experiment_id"] = 1;
        res["epochs"][0]["t"] = 0;
        res["epochs"][0]["dx"] = 0.1;

        return res;
    });

}