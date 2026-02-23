#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
#include <pybind11/stl.h>
#include "App.h"
#include <map>
#include <vector>
#include <string>
#include <atomic>
#include <mutex>
#include <algorithm>
#include <cctype>
#include <sstream>
#include <iomanip>
#include <optional>

namespace py = pybind11;

// --- Helper Functions ---

// Helper to safely destroy Python objects when uWS destroys the lambda without GIL
struct SafeCallback {
    py::function func;
    SafeCallback(py::function f) : func(f) {}
    ~SafeCallback() {
        py::gil_scoped_acquire acquire;
        func = py::function();
    }
};

// Simple URL decoder
std::string url_decode(std::string_view str) {
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

// Cookie helpers
bool is_control_char(char c) {
    return (c >= 0x00 && c <= 0x1f) || c == 0x7f;
}

bool is_cookie_token_char(char c) {
    // ! # $ % & ' * + - . 0-9 A-Z ^ _ ` a-z | ~
    // ASCII only
    if (c < 33 || c > 126) return false;
    if (c == '"' || c == ',' || c == '/' || c == '{' || c == '}' ||
        c == '(' || c == ')' || c == '<' || c == '>' || c == '@' ||
        c == '[' || c == ']' || c == '\\' || c == ':' || c == ';' ||
        c == '=' || c == '?') return false;
    return true;
}

bool needs_quoting(const std::string& value) {
    // Chars allowed without quoting: ! # $ % & ' * + - . : ^ _ ` | ~ and digits/letters
    // Essentially everything except comma, semi-colon, whitespace, backslash, double quote
    for (char c : value) {
        if (c == ' ' || c == '"' || c == ',' || c == ';' || c == '\\') return true;
        if (is_control_char(c)) return true; // Should ideally reject, but here we quote
    }
    return false;
}

std::string format_cookie(std::string name, std::string value,
                          std::optional<int> max_age, std::optional<std::string> expires,
                          std::string path, std::optional<std::string> domain,
                          bool secure, bool http_only, std::optional<std::string> same_site) {

    // Validate name
    for (char c : name) {
        if (!is_cookie_token_char(c)) throw std::invalid_argument("Invalid cookie name");
    }

    // Handle quoting
    if (needs_quoting(value)) {
        if (value.find(';') != std::string::npos) throw std::invalid_argument("Cookie value cannot contain ';'");
        // Simple escaping logic if needed, but RFC 6265 usually just wraps in quotes
        // Python code replaced \ with \\ and " with \"
        std::string escaped;
        for (char c : value) {
            if (c == '\\') escaped += "\\\\";
            else if (c == '"') escaped += "\\\"";
            else escaped += c;
        }
        value = "\"" + escaped + "\"";
    }

    std::stringstream ss;
    ss << name << "=" << value;

    if (max_age.has_value()) {
        ss << "; Max-Age=" << max_age.value();
    }
    if (expires.has_value()) {
        ss << "; Expires=" << expires.value();
    }

    if (!path.empty()) {
        if (path.find(';') != std::string::npos || std::any_of(path.begin(), path.end(), is_control_char))
            throw std::invalid_argument("Invalid characters in Path attribute");
        ss << "; Path=" << path;
    }

    if (domain.has_value()) {
        std::string d = domain.value();
        if (d.find(';') != std::string::npos || std::any_of(d.begin(), d.end(), is_control_char))
            throw std::invalid_argument("Invalid characters in Domain attribute");
        ss << "; Domain=" << d;
    }

    if (secure) ss << "; Secure";
    if (http_only) ss << "; HttpOnly";

    if (same_site.has_value()) {
        std::string s = same_site.value();
        if (s == "None" || s == "none") {
            if (!secure) throw std::invalid_argument("SameSite=None requires Secure=True");
        }
        if (s.find(';') != std::string::npos || std::any_of(s.begin(), s.end(), is_control_char))
            throw std::invalid_argument("Invalid characters in SameSite attribute");
        ss << "; SameSite=" << s;
    }

    std::string result = ss.str();
    if (std::any_of(result.begin(), result.end(), is_control_char)) {
        throw std::invalid_argument("Invalid characters in cookie");
    }
    return result;
}

// Parse path logic
std::pair<std::string, std::vector<std::string>> parse_path(std::string path) {
    std::vector<std::string> param_names;
    std::string native_path = "";

    size_t start = 0;
    while (start < path.length()) {
        size_t end = path.find('/', start);
        if (end == std::string::npos) end = path.length();

        std::string_view segment_view = std::string_view(path).substr(start, end - start);
        std::string segment(segment_view);

        if (!segment.empty()) {
            // Check for {param}
            if (segment.front() == '{' && segment.back() == '}') {
                std::string param_name = segment.substr(1, segment.length() - 2);
                param_names.push_back(param_name);
                native_path += "/:" + param_name;
            } else {
                native_path += "/" + segment;
            }
        }

        start = end + 1;
    }

    if (native_path.empty()) native_path = "/";
    return {native_path, param_names};
}


class Request {
public:
    Request(uWS::HttpRequest *req) {
        url = std::string(req->getUrl());
        method = std::string(req->getMethod());
        query = std::string(req->getQuery());

        int header_count = 0;
        for (auto header : *req) {
            if (++header_count > 100) break; // Limit headers count
            std::string key = std::string(std::get<0>(header));
            std::string value = std::string(std::get<1>(header));
            std::transform(key.begin(), key.end(), key.begin(),
                [](unsigned char c){ return std::tolower(c); });

            if (headers.find(key) != headers.end()) {
                headers[key] += ", " + value;
            } else {
                headers[key] = value;
            }
        }

        for (int i = 0; ; ++i) {
            std::string_view p = req->getParameter(i);
            if (p.length() == 0 && i > 0) break;
            if (p.length() > 0) params.push_back(std::string(p));
            else if (i > 100) break; // sanity check
            else if (i == 0 && p.length() == 0) {
                if (req->getParameter(1).length() == 0) break;
                params.push_back("");
            }
        }
    }
    std::string get_url() { return url; }
    std::string get_method() { return method; }
    std::string get_header(std::string name) {
        if (headers.count(name)) return headers[name];
        return "";
    }
    std::string get_parameter(int index) {
        if (index >= 0 && (size_t)index < params.size()) return params[index];
        return "";
    }
    std::string get_query() { return query; }
    py::dict get_headers() {
        py::dict h;
        for (auto const& [key, val] : headers) h[key.c_str()] = val;
        return h;
    }

    // New: get_queries
    py::dict get_queries() {
        py::dict result;
        std::map<std::string, std::vector<std::string>> query_params;

        size_t start = 0;
        int param_count = 0;
        while (start < query.length()) {
            size_t end = query.find('&', start);
            if (end == std::string::npos) end = query.length();

            if (end > start) {
                // SECURITY: Limit max number of query parameters to 1000 to prevent DoS (CPU/Memory exhaustion)
                if (++param_count > 1000) {
                    throw std::invalid_argument("Too many query parameters (limit 1000)");
                }

                std::string_view pair_view = std::string_view(query).substr(start, end - start);
                size_t eq = pair_view.find('=');
                std::string key, value;

                if (eq != std::string_view::npos) {
                    key = url_decode(pair_view.substr(0, eq));
                    value = url_decode(pair_view.substr(eq + 1));
                } else {
                    key = url_decode(pair_view);
                    value = "";
                }
                query_params[key].push_back(value);
            }
            start = end + 1;
        }

        for (auto const& [k, v] : query_params) {
            py::list l;
            for (const auto& item : v) l.append(item);
            result[k.c_str()] = l;
        }
        return result;
    }

private:
    std::string url;
    std::string method;
    std::string query;
    std::map<std::string, std::string> headers;
    std::vector<std::string> params;
};

class Response {
public:
    Response(uWS::HttpResponse<false> *res, uWS::Loop *loop) : res(res), loop(loop) {
        aborted = std::make_shared<std::atomic<bool>>(false);
        // Cache remote address immediately while we are on the correct thread
        std::string_view addr = res->getRemoteAddress();
        remote_address = std::string(addr);

        res->onAborted([a = aborted]() {
            *a = true;
        });
    }

    void write_status(std::string status) {
        if (*aborted) return;
        loop->defer([res = res, aborted = aborted, status]() {
            if (!*aborted) res->writeStatus(status);
        });
    }

    void write_header(std::string key, std::string value) {
        if (*aborted) return;
        loop->defer([res = res, aborted = aborted, key, value]() {
            if (!*aborted) res->writeHeader(key, value);
        });
    }

    void end(std::string data) {
        if (*aborted) return;
        loop->defer([res = res, aborted = aborted, data]() {
            if (!*aborted) {
                res->end(data);
                *aborted = true; // Mark as aborted/invalid to prevent UAF
            }
        });
    }

    void close() {
        if (*aborted) return;
        loop->defer([res = res, aborted = aborted]() {
            if (!*aborted) {
                res->close();
                *aborted = true; // Mark as aborted/invalid to prevent UAF
            }
        });
    }

    void on_data(py::function callback) {
        if (*aborted) return;
        auto safe_cb = std::make_shared<SafeCallback>(callback);
        // Defer to uWS loop to avoid race condition when calling res->onData from another thread
        loop->defer([res = res, aborted = aborted, safe_cb]() mutable {
            py::gil_scoped_acquire acquire;
            if (!*aborted) {
                res->onData([safe_cb, a = aborted](std::string_view chunk, bool isLast) {
                    if (*a) return;
                    py::gil_scoped_acquire acquire;
                    safe_cb->func(py::bytes(chunk.data(), chunk.length()), isLast);
                });
            }
        });
    }

    void on_aborted(py::function callback) {
        if (*aborted) return;
        auto safe_cb = std::make_shared<SafeCallback>(callback);
        // Defer to uWS loop for thread safety
        loop->defer([res = res, aborted = aborted, safe_cb]() mutable {
            py::gil_scoped_acquire acquire;
            if (!*aborted) {
                res->onAborted([safe_cb, a = aborted]() {
                    *a = true;
                    py::gil_scoped_acquire acquire;
                    safe_cb->func();
                });
            }
        });
    }

    py::bytes get_remote_address_bytes() {
        // Return cached address safely
        return py::bytes(remote_address);
    }

private:
    uWS::HttpResponse<false> *res;
    uWS::Loop *loop;
    std::shared_ptr<std::atomic<bool>> aborted;
    std::string remote_address;
};

class WebSocket {
public:
    WebSocket(uWS::WebSocket<false, true, void *> *ws) : ws(ws) {}
    void send(std::string message, bool is_binary = false) {
        ws->send(message, is_binary ? uWS::OpCode::BINARY : uWS::OpCode::TEXT);
    }
    void close() { ws->close(); }
    void subscribe(std::string topic) { ws->subscribe(topic); }
    void unsubscribe(std::string topic) { ws->unsubscribe(topic); }
    void publish(std::string topic, std::string message, bool is_binary = false, bool compress = false) {
        ws->publish(topic, message, is_binary ? uWS::OpCode::BINARY : uWS::OpCode::TEXT, compress);
    }
    py::bytes get_remote_address_bytes() {
        std::string_view addr = ws->getRemoteAddress();
        return py::bytes(addr.data(), addr.length());
    }

private:
    uWS::WebSocket<false, true, void *> *ws;
};

PYBIND11_MODULE(libxyra, m) {
    m.def("parse_path", &parse_path, "Parse route path");
    m.def("format_cookie", &format_cookie,
          py::arg("name"), py::arg("value"),
          py::arg("max_age") = py::none(), py::arg("expires") = py::none(),
          py::arg("path") = "/", py::arg("domain") = py::none(),
          py::arg("secure") = false, py::arg("http_only") = true,
          py::arg("same_site") = "Lax",
          "Format cookie string");

    py::class_<Request>(m, "Request")
        .def("get_url", &Request::get_url)
        .def("get_method", &Request::get_method)
        .def("get_header", &Request::get_header)
        .def("get_parameter", &Request::get_parameter)
        .def("get_query", &Request::get_query)
        .def("get_headers", &Request::get_headers)
        .def("get_queries", &Request::get_queries);

    py::class_<Response>(m, "Response")
        .def("write_status", &Response::write_status)
        .def("write_header", &Response::write_header)
        .def("end", &Response::end)
        .def("close", &Response::close)
        .def("on_data", &Response::on_data)
        .def("on_aborted", &Response::on_aborted)
        .def("get_remote_address_bytes", &Response::get_remote_address_bytes);

    py::class_<WebSocket>(m, "WebSocket")
        .def("send", &WebSocket::send, py::arg("message"), py::arg("is_binary") = false)
        .def("close", &WebSocket::close)
        .def("subscribe", &WebSocket::subscribe)
        .def("unsubscribe", &WebSocket::unsubscribe)
        .def("publish", &WebSocket::publish, py::arg("topic"), py::arg("message"), py::arg("is_binary") = false, py::arg("compress") = false)
        .def("get_remote_address_bytes", &WebSocket::get_remote_address_bytes);

    py::class_<uWS::App>(m, "App")
        .def(py::init([]() { return new uWS::App(); }))
        .def("get", [](uWS::App &app, std::string pattern, py::function handler) {
            app.get(pattern, [handler](auto *res, auto *req) {
                py::gil_scoped_acquire acquire;
                handler(Response(res, uWS::Loop::get()), Request(req));
            });
            return &app;
        })
        .def("post", [](uWS::App &app, std::string pattern, py::function handler) {
            app.post(pattern, [handler](auto *res, auto *req) {
                py::gil_scoped_acquire acquire;
                handler(Response(res, uWS::Loop::get()), Request(req));
            });
            return &app;
        })
        .def("put", [](uWS::App &app, std::string pattern, py::function handler) {
            app.put(pattern, [handler](auto *res, auto *req) {
                py::gil_scoped_acquire acquire;
                handler(Response(res, uWS::Loop::get()), Request(req));
            });
            return &app;
        })
        .def("del", [](uWS::App &app, std::string pattern, py::function handler) {
            app.del(pattern, [handler](auto *res, auto *req) {
                py::gil_scoped_acquire acquire;
                handler(Response(res, uWS::Loop::get()), Request(req));
            });
            return &app;
        })
        .def("patch", [](uWS::App &app, std::string pattern, py::function handler) {
            app.patch(pattern, [handler](auto *res, auto *req) {
                py::gil_scoped_acquire acquire;
                handler(Response(res, uWS::Loop::get()), Request(req));
            });
            return &app;
        })
        .def("options", [](uWS::App &app, std::string pattern, py::function handler) {
            app.options(pattern, [handler](auto *res, auto *req) {
                py::gil_scoped_acquire acquire;
                handler(Response(res, uWS::Loop::get()), Request(req));
            });
            return &app;
        })
        .def("head", [](uWS::App &app, std::string pattern, py::function handler) {
            app.head(pattern, [handler](auto *res, auto *req) {
                py::gil_scoped_acquire acquire;
                handler(Response(res, uWS::Loop::get()), Request(req));
            });
            return &app;
        })
        .def("any", [](uWS::App &app, std::string pattern, py::function handler) {
            app.any(pattern, [handler](auto *res, auto *req) {
                py::gil_scoped_acquire acquire;
                handler(Response(res, uWS::Loop::get()), Request(req));
            });
            return &app;
        })
        .def("ws", [](uWS::App &app, std::string pattern, py::dict config) {
            uWS::App::WebSocketBehavior<void *> behavior;

            if (config.contains("open")) {
                py::function open_handler = config["open"];
                behavior.open = [open_handler](auto *ws) {
                    py::gil_scoped_acquire acquire;
                    open_handler(WebSocket(ws));
                };
            }
            if (config.contains("message")) {
                py::function message_handler = config["message"];
                behavior.message = [message_handler](auto *ws, std::string_view message, uWS::OpCode opCode) {
                    py::gil_scoped_acquire acquire;
                    message_handler(WebSocket(ws), std::string(message), (int)opCode);
                };
            }
            if (config.contains("close")) {
                py::function close_handler = config["close"];
                behavior.close = [close_handler](auto *ws, int code, std::string_view message) {
                    py::gil_scoped_acquire acquire;
                    close_handler(WebSocket(ws), code, std::string(message));
                };
            }

            app.ws<void *>(pattern, std::move(behavior));
            return &app;
        })
        .def("listen", [](uWS::App &app, int port, py::function callback) {
            app.listen(port, [callback](auto *listen_socket) {
                py::gil_scoped_acquire acquire;
                callback(listen_socket != nullptr);
            });
            return &app;
        })
        .def("run", [](uWS::App &app) {
            py::gil_scoped_release release;
            app.run();
        });
}
