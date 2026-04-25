cmake_minimum_required(VERSION 3.15)
project(gnss_backend)

set(CMAKE_CXX_STANDARD 17)

find_package(Qt6 REQUIRED COMPONENTS Core)

include_directories(
    ${CMAKE_SOURCE_DIR}/Crow/include
    ${CMAKE_SOURCE_DIR}/server
    ${CMAKE_SOURCE_DIR}/inavFramework/src
    /opt/homebrew/include
)

add_executable(server
    server/main.cpp
    server/routes/analyze_routes.cpp
    server/routes/experiment_routes.cpp
    server/services/analysis_service.cpp  
    
#    inavFramework/src/Sp3/reader.cpp
#    inavFramework/src/Sp3/formatchecker.cpp
)

target_link_libraries(server PRIVATE Qt6::Core)