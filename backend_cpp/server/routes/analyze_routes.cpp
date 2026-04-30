#include "analyze_routes.h"
#include "../services/analysis_service.h"

#include <fstream>

void setupAnalyzeRoutes(crow::SimpleApp& app) {

    CROW_ROUTE(app, "/analyze").methods("POST"_method)
    ([](const crow::request& req) {

        crow::multipart::message msg(req);

        auto calc_part = msg.get_part_by_name("calc");
        auto ref_part  = msg.get_part_by_name("ref");
        auto clk_part  = msg.get_part_by_name("clk");

        if (calc_part.body.empty() || ref_part.body.empty()) {
            return crow::response(400, "Files missing");
        }

        std::ofstream("/tmp/calc.sp3") << calc_part.body;
        std::ofstream("/tmp/ref.sp3")  << ref_part.body;

        std::string clk_path = "";

        if (!clk_part.body.empty()) {
            std::ofstream("/tmp/file.clk") << clk_part.body;
            clk_path = "/tmp/file.clk";
        }

        auto result = AnalysisService::analyze(
            "/tmp/calc.sp3",
            "/tmp/ref.sp3",
            clk_path
        );

        return crow::response(result.dump());
    });
}