cmake_minimum_required(VERSION 3.10)
project(xyra_native)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

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

add_library(xyra_native STATIC c_api.cpp ${USOCKETS_SRC})

target_include_directories(xyra_native PRIVATE
    ../uWebSockets/src
    ../uWebSockets/uSockets/src
)

# Platform specific settings
if(WIN32)
    find_package(libuv CONFIG REQUIRED)
    target_compile_definitions(xyra_native PRIVATE LIBUS_USE_LIBUV)
    if(TARGET libuv::uv)
        target_link_libraries(xyra_native PRIVATE libuv::uv)
    elseif(TARGET libuv::uv_a)
        target_link_libraries(xyra_native PRIVATE libuv::uv_a)
    elseif(TARGET libuv::libuv)
        target_link_libraries(xyra_native PRIVATE libuv::libuv)
    else()
        target_link_libraries(xyra_native PRIVATE libuv)
    endif()
elseif(APPLE)
    target_compile_definitions(xyra_native PRIVATE LIBUS_USE_KQUEUE)
else()
    target_compile_definitions(xyra_native PRIVATE LIBUS_USE_EPOLL)
endif()

target_compile_definitions(xyra_native PRIVATE LIBUS_NO_SSL)

target_link_libraries(xyra_native PRIVATE ZLIB::ZLIB)

set_target_properties(xyra_native PROPERTIES POSITION_INDEPENDENT_CODE ON)
set_target_properties(xyra_native PROPERTIES PREFIX "lib")
set_target_properties(xyra_native PROPERTIES OUTPUT_NAME "xyra")

# We need to compile uSockets as a static library and link it into our shared library
# Actually USOCKETS_SRC is already compiled in. BUT the problem is that 'us_socket_write' etc
# are missing. Let's make sure uSockets uses the correct compile definitions globally.
if(WIN32)
    target_compile_definitions(xyra_native PUBLIC LIBUS_USE_LIBUV)
elseif(APPLE)
    target_compile_definitions(xyra_native PUBLIC LIBUS_USE_KQUEUE)
else()
    target_compile_definitions(xyra_native PUBLIC LIBUS_USE_EPOLL)
endif()

# Build the uWebSockets source file
set(UWS_SRC
    ../uWebSockets/src/App.h
)
