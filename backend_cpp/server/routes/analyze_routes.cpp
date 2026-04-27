#include "analyze_routes.h"
#include "../services/analysis_service.h"

void setupAnalyzeRoutes(crow::SimpleApp& app)
{
    CROW_ROUTE(app, "/analyze")
    .methods("POST"_method)
    ([]() {

        auto result = AnalysisService::analyze("calc.sp3", "ref.sp3");

        return crow::response(result.dump());
    });
}