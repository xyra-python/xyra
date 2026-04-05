#include "c_api.h"
#include "App.h"
#include <string>
#include <string_view>
#include <atomic>
#include <memory>
#include <mutex>
#include <algorithm>
#include <cctype>
#include <sstream>
#include <iomanip>
#include <iostream>
#include <cstring>
#include <vector>

// --- Utility Functions from bindings.cpp ---
static bool cpp_has_control_chars(std::string_view s) {
    return std::any_of(s.begin(), s.end(), [](unsigned char c) {
        return std::iscntrl(c) && c != '\t';
    });
}

static std::string url_decode(std::string_view str) {
    std::string ret;
    ret.reserve(str.length());
    for (size_t i = 0; i < str.length(); ++i) {
        if (str[i] == '%') {
            if (i + 2 < str.length()) {
                int value;
                std::istringstream is(std::string(str.substr(i + 1, 2)));
                if (is >> std::hex >> value) {
                    if (value == 0) {
                        ret += '?'; // SECURITY: sanitize null byte
                    } else {
                        ret += static_cast<char>(value);
                    }
                    i += 2;
                } else {
                    ret += '%'; // invalid hex, keep as is
                }
            } else {
                ret += '%';
            }
        } else if (str[i] == '+') {
            ret += ' ';
        } else {
            ret += str[i];
        }
    }
    return ret;
}

// --- C API Implementation ---
extern "C" {

bool xyra_has_control_chars(const char* str, size_t len) {
    return cpp_has_control_chars(std::string_view(str, len));
}

void xyra_parse_path(const char* path_c, size_t len, void* user_data, void (*cb)(void*, const char*, size_t, const char*, size_t)) {
    std::string_view path(path_c, len);
    size_t start = 0;
    while (start < path.length()) {
        size_t colon = path.find(':', start);
        if (colon == std::string_view::npos) break;

        size_t end = path.find('/', colon);
        if (end == std::string_view::npos) end = path.length();

        std::string param_name(path.substr(colon + 1, end - colon - 1));
        std::string pattern_type = "str";

        size_t hyphen = param_name.find('-');
        if (hyphen != std::string::npos) {
            pattern_type = param_name.substr(hyphen + 1);
            param_name = param_name.substr(0, hyphen);
        }

        cb(user_data, param_name.data(), param_name.size(), pattern_type.data(), pattern_type.size());
        start = end;
    }
}

void xyra_parse_qsl(const char* query_c, size_t len, bool keep_blank_values, int max_num_fields, void* user_data, void (*cb)(void*, const char*, size_t, const char*, size_t)) {
    std::string_view query(query_c, len);
    size_t start = 0;
    int param_count = 0;

    while (start < query.length()) {
        size_t end = query.find('&', start);
        if (end == std::string_view::npos) end = query.length();

        if (end > start || keep_blank_values) {
            if (++param_count > max_num_fields) {
                // Ignore the rest or throw? We'll just stop parsing here for C API.
                break;
            }

            std::string_view pair_view = query.substr(start, end - start);
            size_t eq = pair_view.find('=');
            std::string key, value;

            if (eq != std::string_view::npos) {
                key = url_decode(pair_view.substr(0, eq));
                value = url_decode(pair_view.substr(eq + 1));
            } else {
                key = url_decode(pair_view);
                value = "";
            }

            if (!key.empty() || keep_blank_values) {
                cb(user_data, key.data(), key.size(), value.data(), value.size());
            }
        }
        start = end + 1;
    }
}

void xyra_format_cookie(
    const char* name, const char* value,
    int has_max_age, int max_age,
    const char* expires,
    const char* path,
    const char* domain,
    bool secure, bool http_only,
    const char* same_site,
    char* out_buffer, size_t* out_len
) {
    std::string s_name(name);
    std::string s_value(value);

    // SECURITY checks exactly as they were in format_cookie bindings
    if (s_name.find('\r') != std::string::npos || s_name.find('\n') != std::string::npos || s_name.find(' ') != std::string::npos || s_name.find(';') != std::string::npos || s_name.find('=') != std::string::npos ||
        s_value.find('\r') != std::string::npos || s_value.find('\n') != std::string::npos) {
        // We handle this via exception or returning 0 and letting Python handle it.
        // Let's return error by setting out_len = 0 and writing error prefix
        *out_len = 0;
        return;
    }

    if (s_value.find(';') != std::string::npos) {
        // Semicolon rejection
        *out_len = (size_t)-1;
        return;
    }

    if (path && (strchr(path, '\r') || strchr(path, '\n') || strchr(path, ';'))) { *out_len = (size_t)-2; return; }
    if (domain && (strchr(domain, '\r') || strchr(domain, '\n') || strchr(domain, ';'))) { *out_len = (size_t)-2; return; }
    if (same_site && (strchr(same_site, '\r') || strchr(same_site, '\n') || strchr(same_site, ';'))) { *out_len = (size_t)-2; return; }

    std::string cookie = s_name + "=" + s_value;

    if (has_max_age) {
        cookie += "; Max-Age=" + std::to_string(max_age);
    }
    if (expires && strlen(expires) > 0) {
        cookie += "; Expires=" + std::string(expires);
    }
    if (path && strlen(path) > 0) {
        cookie += "; Path=" + std::string(path);
    }
    if (domain && strlen(domain) > 0) {
        cookie += "; Domain=" + std::string(domain);
    }
    if (secure) {
        cookie += "; Secure";
    }
    if (http_only) {
        cookie += "; HttpOnly";
    }
    if (same_site && strlen(same_site) > 0) {
        cookie += "; SameSite=" + std::string(same_site);
    }

    if (cookie.size() < *out_len) {
        std::memcpy(out_buffer, cookie.data(), cookie.size());
        out_buffer[cookie.size()] = '\0';
        *out_len = cookie.size();
    } else {
        *out_len = 0; // buffer too small
    }
}

// --- Wrappers for App, Request, Response, WebSocket ---

struct WebSocketData {
    std::shared_ptr<std::atomic<bool>> is_closed;
    WebSocketData() : is_closed(std::make_shared<std::atomic<bool>>(false)) {}
};

struct xyra_request {
    uWS::HttpRequest *req;
    bool headers_truncated;
};

struct xyra_response {
    uWS::HttpResponse<false> *res;
    uWS::Loop *loop;
    std::shared_ptr<std::atomic<bool>> aborted;
    std::string remote_address;
};

struct xyra_websocket {
    uWS::WebSocket<false, true, WebSocketData> *ws;
    std::shared_ptr<std::atomic<bool>> is_closed;
};

xyra_app_t* xyra_app_create(void) {
    return reinterpret_cast<xyra_app_t*>(new uWS::App());
}

void xyra_app_destroy(xyra_app_t* app) {
    delete reinterpret_cast<uWS::App*>(app);
}

// Route handlers macro
#define ROUTE_HANDLER(METHOD) \
void xyra_app_##METHOD(xyra_app_t* app, const char* pattern, xyra_route_handler_cb handler, void* user_data) { \
    reinterpret_cast<uWS::App*>(app)->METHOD(pattern, [handler, user_data](auto *res, auto *req) { \
        xyra_request req_wrapper{req, false}; \
        xyra_response res_wrapper{res, uWS::Loop::get(), std::make_shared<std::atomic<bool>>(false), std::string(res->getRemoteAddressAsText())}; \
        res->onAborted([&res_wrapper]() { \
            *res_wrapper.aborted = true; \
        }); \
        handler(&res_wrapper, &req_wrapper, user_data); \
    }); \
}

ROUTE_HANDLER(get)
ROUTE_HANDLER(post)
ROUTE_HANDLER(put)
ROUTE_HANDLER(del)
ROUTE_HANDLER(patch)
ROUTE_HANDLER(options)
ROUTE_HANDLER(head)
ROUTE_HANDLER(any)

void xyra_app_ws(xyra_app_t* app, const char* pattern,
                 xyra_ws_open_cb open_cb,
                 xyra_ws_message_cb message_cb,
                 xyra_ws_upgrade_cb upgrade_cb,
                 xyra_ws_close_cb close_cb,
                 void* user_data) {

    uWS::App::WebSocketBehavior<WebSocketData> behavior;

    if (open_cb) {
        behavior.open = [open_cb, user_data](auto *ws) {
            xyra_websocket ws_wrapper{ws, ws->getUserData()->is_closed};
            open_cb(&ws_wrapper, user_data);
        };
    }

    if (message_cb) {
        behavior.message = [message_cb, user_data](auto *ws, std::string_view message, uWS::OpCode opCode) {
            xyra_websocket ws_wrapper{ws, ws->getUserData()->is_closed};
            message_cb(&ws_wrapper, message.data(), message.size(), (int)opCode, user_data);
        };
    }

    if (upgrade_cb) {
        behavior.upgrade = [upgrade_cb, user_data](auto *res, auto *req, auto *context) {
            bool aborted = false;
            res->onAborted([&aborted]() { aborted = true; });

            xyra_request req_wrapper{req, false};
            xyra_response res_wrapper{res, uWS::Loop::get(), std::make_shared<std::atomic<bool>>(false), std::string(res->getRemoteAddressAsText())};

            bool ok = upgrade_cb(&res_wrapper, &req_wrapper, user_data);

            if (aborted) return;

            if (ok) {
                std::string_view secWebSocketKey = req->getHeader("sec-websocket-key");
                std::string_view secWebSocketProtocol = req->getHeader("sec-websocket-protocol");
                std::string_view secWebSocketExtensions = req->getHeader("sec-websocket-extensions");

                res->template upgrade<WebSocketData>(
                    {},
                    secWebSocketKey,
                    secWebSocketProtocol,
                    secWebSocketExtensions,
                    context
                );
            } else {
                res->writeStatus("403 Forbidden");
                res->end("Cross-Site WebSocket Hijacking blocked by Xyra");
            }
        };
    }

    behavior.close = [close_cb, user_data](auto *ws, int code, std::string_view message) {
        *ws->getUserData()->is_closed = true;
        if (close_cb) {
            xyra_websocket ws_wrapper{ws, ws->getUserData()->is_closed};
            close_cb(&ws_wrapper, code, message.data(), message.size(), user_data);
        }
    };

    reinterpret_cast<uWS::App*>(app)->ws<WebSocketData>(pattern, std::move(behavior));
}

void xyra_app_listen(xyra_app_t* app, int port, xyra_listen_cb cb, void* user_data) {
    reinterpret_cast<uWS::App*>(app)->listen(port, [cb, user_data](auto *listen_socket) {
        cb(listen_socket != nullptr, user_data);
    });
}

void xyra_app_run(xyra_app_t* app) {
    reinterpret_cast<uWS::App*>(app)->run();
}

// --- Request ---
size_t xyra_req_get_url(xyra_request_t* req, const char** out_url) {
    std::string_view url = req->req->getUrl();
    *out_url = url.data();
    return url.length();
}

size_t xyra_req_get_method(xyra_request_t* req, const char** out_method) {
    std::string_view method = req->req->getMethod();
    *out_method = method.data();
    return method.length();
}

size_t xyra_req_get_header(xyra_request_t* req, const char* key, const char** out_value) {
    std::string_view val = req->req->getHeader(key);
    *out_value = val.data();
    return val.length();
}

size_t xyra_req_get_parameter(xyra_request_t* req, int index, const char** out_param) {
    std::string_view param = req->req->getParameter(index);
    *out_param = param.data();
    return param.length();
}

size_t xyra_req_get_query(xyra_request_t* req, const char* key, const char** out_value) {
    std::string_view val = req->req->getQuery(key);
    *out_value = val.data();
    return val.length();
}

void xyra_req_get_headers(xyra_request_t* req, void* user_data, void (*cb)(void*, const char*, size_t, const char*, size_t)) {
    int count = 0;
    for (auto [key, value] : *req->req) {
        if (++count > 100) {
            req->headers_truncated = true;
            break;
        }
        cb(user_data, key.data(), key.length(), value.data(), value.length());
    }
}

void xyra_req_get_queries(xyra_request_t* req, void* user_data, void (*cb)(void*, const char*, size_t, const char*, size_t)) {
    std::string_view query = req->req->getQuery();
    if (query.empty()) return;

    // Use the same logic as parse_qsl_cpp
    xyra_parse_qsl(query.data(), query.length(), true, 1000, user_data, cb);
}

bool xyra_req_get_headers_truncated(xyra_request_t* req) {
    return req->headers_truncated;
}

// --- Response ---
void xyra_res_write_status(xyra_response_t* res, const char* status, size_t len) {
    if (*res->aborted) return;
    res->res->writeStatus(std::string_view(status, len));
}

void xyra_res_write_header(xyra_response_t* res, const char* key, size_t key_len, const char* value, size_t value_len) {
    if (*res->aborted) return;
    res->res->writeHeader(std::string_view(key, key_len), std::string_view(value, value_len));
}

void xyra_res_end(xyra_response_t* res, const char* data, size_t len, bool close_connection) {
    if (*res->aborted) return;
    res->res->end(std::string_view(data, len), close_connection);
}

void xyra_res_close(xyra_response_t* res) {
    if (*res->aborted) return;
    res->res->close();
}

struct ResDataCtx {
    xyra_res_on_data_cb cb;
    void* user_data;
};

void xyra_res_on_data(xyra_response_t* res, xyra_res_on_data_cb cb, void* user_data) {
    if (*res->aborted) return;
    res->res->onData([cb, user_data](std::string_view chunk, bool isEnd) {
        cb(chunk.data(), chunk.length(), isEnd, user_data);
    });
}

void xyra_res_on_aborted(xyra_response_t* res, xyra_res_on_aborted_cb cb, void* user_data) {
    if (*res->aborted) {
        cb(user_data);
        return;
    }
    res->res->onAborted([cb, user_data, res]() {
        *res->aborted = true;
        cb(user_data);
    });
}

size_t xyra_res_get_remote_address_bytes(xyra_response_t* res, const char** out_addr) {
    *out_addr = res->remote_address.data();
    return res->remote_address.length();
}

// --- WebSocket ---
void xyra_ws_send(xyra_websocket_t* ws, const char* message, size_t len, bool is_binary) {
    if (*ws->is_closed) return;
    ws->ws->send(std::string_view(message, len), is_binary ? uWS::OpCode::BINARY : uWS::OpCode::TEXT);
}

void xyra_ws_close(xyra_websocket_t* ws) {
    if (*ws->is_closed) return;
    ws->ws->close();
}

void xyra_ws_subscribe(xyra_websocket_t* ws, const char* topic, size_t len) {
    if (*ws->is_closed) return;
    ws->ws->subscribe(std::string_view(topic, len));
}

void xyra_ws_unsubscribe(xyra_websocket_t* ws, const char* topic, size_t len) {
    if (*ws->is_closed) return;
    ws->ws->unsubscribe(std::string_view(topic, len));
}

void xyra_ws_publish(xyra_websocket_t* ws, const char* topic, size_t topic_len, const char* message, size_t msg_len, bool is_binary, bool compress) {
    if (*ws->is_closed) return;
    ws->ws->publish(std::string_view(topic, topic_len), std::string_view(message, msg_len), is_binary ? uWS::OpCode::BINARY : uWS::OpCode::TEXT, compress);
}

size_t xyra_ws_get_remote_address_bytes(xyra_websocket_t* ws, const char** out_addr) {
    if (*ws->is_closed) {
        *out_addr = nullptr;
        return 0;
    }
    std::string_view addr = ws->ws->getRemoteAddress();
    *out_addr = addr.data();
    return addr.length();
}

} // extern "C"
