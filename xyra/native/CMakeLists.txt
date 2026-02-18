cmake_minimum_required(VERSION 3.10)
project(xyra_native)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find pybind11
find_package(pybind11 REQUIRED)
# Find ZLIB
find_package(ZLIB REQUIRED)

# uSockets sources (common)
set(USOCKETS_SRC
    ../uWebSockets/uSockets/src/bsd.c
    ../uWebSockets/uSockets/src/context.c
    ../uWebSockets/uSockets/src/loop.c
    ../uWebSockets/uSockets/src/socket.c
    ../uWebSockets/uSockets/src/udp.c
)

if(WIN32)
    list(APPEND USOCKETS_SRC ../uWebSockets/uSockets/src/eventing/libuv.c)
else()
    list(APPEND USOCKETS_SRC ../uWebSockets/uSockets/src/eventing/epoll_kqueue.c)
endif()

add_library(xyra_native MODULE bindings.cpp ${USOCKETS_SRC})

target_include_directories(xyra_native PRIVATE
    ../uWebSockets/src
    ../uWebSockets/uSockets/src
)

# Platform specific settings
if(WIN32)
    find_package(libuv CONFIG REQUIRED)
    target_compile_definitions(xyra_native PRIVATE LIBUS_USE_LIBUV)
    target_link_libraries(xyra_native PRIVATE libuv::libuv)
elseif(APPLE)
    target_compile_definitions(xyra_native PRIVATE LIBUS_USE_KQUEUE)
else()
    target_compile_definitions(xyra_native PRIVATE LIBUS_USE_EPOLL)
endif()

target_compile_definitions(xyra_native PRIVATE LIBUS_NO_SSL)

target_link_libraries(xyra_native PRIVATE pybind11::module ZLIB::ZLIB)

set_target_properties(xyra_native PROPERTIES PREFIX "")
set_target_properties(xyra_native PROPERTIES OUTPUT_NAME "libxyra")
if(NOT WIN32)
    set_target_properties(xyra_native PROPERTIES SUFFIX ".so")
endif()
