cmake_minimum_required(VERSION 3.15)
project(gnss_backend)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_INCLUDE_CURRENT_DIR ON)

# Находим необходимые компоненты Qt6
find_package(Qt6 REQUIRED COMPONENTS Core Network Sql WebSockets)

# Определяем пути
set(INAV_ROOT ${CMAKE_SOURCE_DIR}/inavFramework)
set(THIRDPARTY_ROOT ${INAV_ROOT}/3rdparty)

# Собираем все исходники inavFramework, исключая main.cpp
file(GLOB_RECURSE INAV_SOURCES
    ${INAV_ROOT}/src/*.cpp
)

# Исключаем все main.cpp файлы
list(FILTER INAV_SOURCES EXCLUDE REGEX ".*/main\\.cpp$")

# Исключаем проблемные файлы
list(FILTER INAV_SOURCES EXCLUDE REGEX ".*/RINEX/formatchecker\\.cpp$")
list(FILTER INAV_SOURCES EXCLUDE REGEX ".*/WebSocketServer/.*\\.cpp$")
list(FILTER INAV_SOURCES EXCLUDE REGEX ".*/SBAS/.*\\.cpp$")  # Исключаем SBAS из-за конфликта макросов

# Добавляем исходники 3rdparty библиотек
file(GLOB QFTP_SOURCES
    ${THIRDPARTY_ROOT}/QFtp/*.cpp
)
file(GLOB MATRIX_SOURCES
    ${THIRDPARTY_ROOT}/Matrix/*.cpp
)

# Объединяем все исходники
list(APPEND INAV_SOURCES ${QFTP_SOURCES} ${MATRIX_SOURCES})

# Создаем статическую библиотеку inav_framework
add_library(inav_framework STATIC ${INAV_SOURCES})

# Настройка AUTOMOC для библиотеки (БЕЗ лишних опций)
set_target_properties(inav_framework PROPERTIES
    AUTOMOC ON
    AUTOUIC ON
    AUTORCC ON
)

# Добавляем include директории
target_include_directories(inav_framework PUBLIC
    ${INAV_ROOT}
    ${INAV_ROOT}/src
    ${INAV_ROOT}/include
    ${THIRDPARTY_ROOT}
)

# Линкуем библиотеки к inav_framework
target_link_libraries(inav_framework 
    Qt6::Core 
    Qt6::Network 
    Qt6::Sql
    Qt6::WebSockets
)

# Создаем исполняемый файл сервера
add_executable(server
    server/main.cpp
    server/routes/analyze_routes.cpp
    server/routes/experiment_routes.cpp
    server/services/analysis_service.cpp  
    server/services/clk_parser.cpp
    ${INAV_ROOT}/src/Sp3/reader.cpp
)

# Добавляем include директории для сервера
target_include_directories(server PRIVATE
    ${CMAKE_SOURCE_DIR}/Crow/include
    ${CMAKE_SOURCE_DIR}/server
    ${INAV_ROOT}
    ${INAV_ROOT}/src
    ${INAV_ROOT}/include
    ${THIRDPARTY_ROOT}
    /opt/homebrew/include
)

# Линкуем библиотеки к серверу
target_link_libraries(server PRIVATE 
    inav_framework 
    Qt6::Core 
    Qt6::Network 
    Qt6::Sql
    Qt6::WebSockets
)

find_package(nlohmann_json REQUIRED)
target_link_libraries(server PRIVATE Qt6::Core nlohmann_json::nlohmann_json)

# Для macOS: линкуем дополнительные фреймворки если нужно
if(APPLE)
    target_link_libraries(server PRIVATE
        "-framework Foundation"
        "-framework Security"
    )
endif()