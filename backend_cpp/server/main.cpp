#include "crow.h"
#include "routes/analyze_routes.h"
#include "routes/experiment_routes.h"

int main() {
    crow::SimpleApp app;

    register_analyze_routes(app);
    register_experiment_routes(app);

    app.port(8080).run();
}