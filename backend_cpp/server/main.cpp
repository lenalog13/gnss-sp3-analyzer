#include "crow.h"
#include "routes/analyze_routes.h"
#include "routes/experiment_routes.h"

int main() {
    crow::SimpleApp app;

    // ROOT (чтобы не было 404)
    CROW_ROUTE(app, "/")
    ([](){
        return "GNSS Backend is running";
    });

    setupAnalyzeRoutes(app);
    setupExperimentRoutes(app);

    app.port(8080).multithreaded().run();
}