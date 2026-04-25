cmake_minimum_required(VERSION 3.15)
project(gnss_backend)

set(CMAKE_CXX_STANDARD 17)

include_directories(
    ${CMAKE_SOURCE_DIR}/Crow/include
    ${CMAKE_SOURCE_DIR}/server
    /opt/homebrew/include
)

add_executable(server
    server/main.cpp
    server/routes/analyze_routes.cpp
    server/routes/experiment_routes.cpp
)