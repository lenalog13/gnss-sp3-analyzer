#include "analyze_routes.h"
#include "../services/analysis_service.h"

#include <fstream>
#include <string>

void setupAnalyzeRoutes(crow::SimpleApp& app) {

    CROW_ROUTE(app, "/analyze").methods(crow::HTTPMethod::Post)
    ([](const crow::request& req) {

        crow::multipart::message msg(req);

        auto calc_part = msg.get_part_by_name("calc");
        auto ref_part  = msg.get_part_by_name("ref");

        // ===== Проверка =====
        if (calc_part.body.empty() || ref_part.body.empty()) {
            return crow::response(400, R"({"error":"files missing"})");
        }

        // ===== Пути (лучше временные) =====
        std::string calc_path = "/tmp/calc.sp3";
        std::string ref_path  = "/tmp/ref.sp3";

        // ===== Сохраняем БИНАРНО =====
        {
            std::ofstream f(calc_path, std::ios::binary);
            if (!f) {
                return crow::response(500, R"({"error":"cannot write calc"})");
            }
            f.write(calc_part.body.c_str(), calc_part.body.size());
        }

        {
            std::ofstream f(ref_path, std::ios::binary);
            if (!f) {
                return crow::response(500, R"({"error":"cannot write ref"})");
            }
            f.write(ref_part.body.c_str(), ref_part.body.size());
        }

        // ===== Анализ =====
        auto result = AnalysisService::analyze(calc_path, ref_path);

        // ===== JSON ответ =====
        crow::response res;
        res.code = 200;
        res.set_header("Content-Type", "application/json");
        res.write(result.dump());

        std::cout << "calc size: " << calc_part.body.size() << std::endl;
        std::cout << "ref size: " << ref_part.body.size() << std::endl;

        return res;
    });
}