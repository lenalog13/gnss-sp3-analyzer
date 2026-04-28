#include "analyze_routes.h"
#include "../services/analysis_service.h"

#include <fstream>

void setupAnalyzeRoutes(crow::SimpleApp& app) {

    CROW_ROUTE(app, "/analyze").methods("POST"_method)

    ([](const crow::request& req) {

        crow::multipart::message msg(req);

        auto calc_part = msg.get_part_by_name("calc");

        auto ref_part  = msg.get_part_by_name("ref");

        if (calc_part.body.empty() || ref_part.body.empty()) {

            return crow::response(400, "Files missing");

        }

        std::string calc_data = calc_part.body;

        std::string ref_data  = ref_part.body;

        std::ofstream("calc.sp3") << calc_data;

        std::ofstream("ref.sp3")  << ref_data;

        auto result = AnalysisService::analyze("calc.sp3", "ref.sp3");

        return crow::response(result.dump());
    });
}

