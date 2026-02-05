#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
#include <pybind11/stl.h>
#include "App.h"
#include <map>
#include <vector>
#include <string>
#include <atomic>
#include <mutex>

namespace py = pybind11;

class Request {
public:
    Request(uWS::HttpRequest *req) {
        url = std::string(req->getUrl());
        method = std::string(req->getMethod());
        query = std::string(req->getQuery());

        for (auto header : *req) {
            headers[std::string(std::get<0>(header))] = std::string(std::get<1>(header));
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
        res->onAborted([a = aborted]() {
            *a = true;
        });
    }

    void write_status(std::string status) {
        if (*aborted) return;
        loop->defer([this, status]() {
            if (!*aborted) res->writeStatus(status);
        });
    }

    void write_header(std::string key, std::string value) {
        if (*aborted) return;
        loop->defer([this, key, value]() {
            if (!*aborted) res->writeHeader(key, value);
        });
    }

    void end(std::string data) {
        if (*aborted) return;
        loop->defer([this, data]() {
            if (!*aborted) res->end(data);
        });
    }

    void on_data(py::function callback) {
        if (*aborted) return;
        res->onData([callback, a = aborted](std::string_view chunk, bool isLast) {
            if (*a) return;
            py::gil_scoped_acquire acquire;
            callback(py::bytes(chunk.data(), chunk.length()), isLast);
        });
    }

    void on_aborted(py::function callback) {
        res->onAborted([callback, a = aborted]() {
            *a = true;
            py::gil_scoped_acquire acquire;
            callback();
        });
    }

    py::bytes get_remote_address_bytes() {
        if (*aborted) return py::bytes("");
        std::string_view addr = res->getRemoteAddress();
        return py::bytes(addr.data(), addr.length());
    }

private:
    uWS::HttpResponse<false> *res;
    uWS::Loop *loop;
    std::shared_ptr<std::atomic<bool>> aborted;
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
    py::class_<Request>(m, "Request")
        .def("get_url", &Request::get_url)
        .def("get_method", &Request::get_method)
        .def("get_header", &Request::get_header)
        .def("get_parameter", &Request::get_parameter)
        .def("get_query", &Request::get_query)
        .def("get_headers", &Request::get_headers);

    py::class_<Response>(m, "Response")
        .def("write_status", &Response::write_status)
        .def("write_header", &Response::write_header)
        .def("end", &Response::end)
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
