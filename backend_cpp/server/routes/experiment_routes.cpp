#include "experiment_routes.h"

void register_experiment_routes(crow::SimpleApp& app) {

    CROW_ROUTE(app, "/experiments")
    ([](){
        crow::json::wvalue res;

        res[0]["id"] = 1;
        res[0]["name"] = "Test";

        return res;
    });

    CROW_ROUTE(app, "/experiment/<int>")
    ([](int id){
        crow::json::wvalue res;

        res["id"] = id;
        res["epochs"][0]["dx"] = 0.1;

        return res;
    });
}