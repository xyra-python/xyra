cmake_minimum_required(VERSION 3.10)
project(xyra_native)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find pybind11
find_package(pybind11 REQUIRED)
# Find ZLIB
find_package(ZLIB REQUIRED)

# uSockets sources
set(USOCKETS_SRC
    ../uWebSockets/uSockets/src/bsd.c
    ../uWebSockets/uSockets/src/context.c
    ../uWebSockets/uSockets/src/loop.c
    ../uWebSockets/uSockets/src/socket.c
    ../uWebSockets/uSockets/src/udp.c
    ../uWebSockets/uSockets/src/eventing/epoll_kqueue.c
)

add_library(xyra_native MODULE bindings.cpp ${USOCKETS_SRC})

target_include_directories(xyra_native PRIVATE
    ../uWebSockets/src
    ../uWebSockets/uSockets/src
)

# Use Epoll on Linux
if(APPLE)
    target_compile_definitions(xyra_native PRIVATE LIBUS_USE_KQUEUE)
else()
    target_compile_definitions(xyra_native PRIVATE LIBUS_USE_EPOLL)
endif()

target_compile_definitions(xyra_native PRIVATE LIBUS_NO_SSL)

target_link_libraries(xyra_native PRIVATE pybind11::module ZLIB::ZLIB)

set_target_properties(xyra_native PROPERTIES PREFIX "")
set_target_properties(xyra_native PROPERTIES OUTPUT_NAME "libxyra")
set_target_properties(xyra_native PROPERTIES SUFFIX ".so")
