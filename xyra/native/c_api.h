#ifndef XYRA_C_API_H
#define XYRA_C_API_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations for opaque types
typedef struct xyra_app xyra_app_t;
typedef struct xyra_request xyra_request_t;
typedef struct xyra_response xyra_response_t;
typedef struct xyra_websocket xyra_websocket_t;

// Utility functions
bool xyra_has_control_chars(const char* str, size_t len);
void xyra_parse_path(const char* path, size_t len, void* user_data, void (*cb)(void*, const char*, size_t, const char*, size_t));
void xyra_parse_qsl(const char* query, size_t len, bool keep_blank_values, int max_num_fields, void* user_data, void (*cb)(void*, const char*, size_t, const char*, size_t));
void xyra_format_cookie(
    const char* name, const char* value,
    int has_max_age, int max_age,
    const char* expires,
    const char* path,
    const char* domain,
    bool secure, bool http_only,
    const char* same_site,
    char* out_buffer, size_t* out_len
);

// App functions
xyra_app_t* xyra_app_create(void);
void xyra_app_destroy(xyra_app_t* app);

// Callbacks
typedef void (*xyra_route_handler_cb)(xyra_response_t* res, xyra_request_t* req, void* user_data);

void xyra_app_get(xyra_app_t* app, const char* pattern, xyra_route_handler_cb handler, void* user_data);
void xyra_app_post(xyra_app_t* app, const char* pattern, xyra_route_handler_cb handler, void* user_data);
void xyra_app_put(xyra_app_t* app, const char* pattern, xyra_route_handler_cb handler, void* user_data);
void xyra_app_del(xyra_app_t* app, const char* pattern, xyra_route_handler_cb handler, void* user_data);
void xyra_app_patch(xyra_app_t* app, const char* pattern, xyra_route_handler_cb handler, void* user_data);
void xyra_app_options(xyra_app_t* app, const char* pattern, xyra_route_handler_cb handler, void* user_data);
void xyra_app_head(xyra_app_t* app, const char* pattern, xyra_route_handler_cb handler, void* user_data);
void xyra_app_any(xyra_app_t* app, const char* pattern, xyra_route_handler_cb handler, void* user_data);

typedef void (*xyra_ws_open_cb)(xyra_websocket_t* ws, void* user_data);
typedef void (*xyra_ws_message_cb)(xyra_websocket_t* ws, const char* message, size_t len, int opCode, void* user_data);
typedef bool (*xyra_ws_upgrade_cb)(xyra_response_t* res, xyra_request_t* req, void* user_data);
typedef void (*xyra_ws_close_cb)(xyra_websocket_t* ws, int code, const char* message, size_t len, void* user_data);

void xyra_app_ws(xyra_app_t* app, const char* pattern,
                 xyra_ws_open_cb open_cb,
                 xyra_ws_message_cb message_cb,
                 xyra_ws_upgrade_cb upgrade_cb,
                 xyra_ws_close_cb close_cb,
                 void* user_data);

typedef void (*xyra_listen_cb)(bool success, void* user_data);
void xyra_app_listen(xyra_app_t* app, int port, xyra_listen_cb cb, void* user_data);
void xyra_app_run(xyra_app_t* app);

// Request functions
size_t xyra_req_get_url(xyra_request_t* req, const char** out_url);
size_t xyra_req_get_method(xyra_request_t* req, const char** out_method);
size_t xyra_req_get_header(xyra_request_t* req, const char* key, const char** out_value);
size_t xyra_req_get_parameter(xyra_request_t* req, int index, const char** out_param);
size_t xyra_req_get_query(xyra_request_t* req, const char* key, const char** out_value);
void xyra_req_get_headers(xyra_request_t* req, void* user_data, void (*cb)(void*, const char*, size_t, const char*, size_t));
void xyra_req_get_queries(xyra_request_t* req, void* user_data, void (*cb)(void*, const char*, size_t, const char*, size_t));
bool xyra_req_get_headers_truncated(xyra_request_t* req);

// Response functions
void xyra_res_write_status(xyra_response_t* res, const char* status, size_t len);
void xyra_res_write_header(xyra_response_t* res, const char* key, size_t key_len, const char* value, size_t value_len);
void xyra_res_end(xyra_response_t* res, const char* data, size_t len, bool close_connection);
void xyra_res_close(xyra_response_t* res);

typedef void (*xyra_res_on_data_cb)(const char* chunk, size_t len, bool is_end, void* user_data);
void xyra_res_on_data(xyra_response_t* res, xyra_res_on_data_cb cb, void* user_data);

typedef void (*xyra_res_on_aborted_cb)(void* user_data);
void xyra_res_on_aborted(xyra_response_t* res, xyra_res_on_aborted_cb cb, void* user_data);

size_t xyra_res_get_remote_address_bytes(xyra_response_t* res, const char** out_addr);

// WebSocket functions
void xyra_ws_send(xyra_websocket_t* ws, const char* message, size_t len, bool is_binary);
void xyra_ws_close(xyra_websocket_t* ws);
void xyra_ws_subscribe(xyra_websocket_t* ws, const char* topic, size_t len);
void xyra_ws_unsubscribe(xyra_websocket_t* ws, const char* topic, size_t len);
void xyra_ws_publish(xyra_websocket_t* ws, const char* topic, size_t topic_len, const char* message, size_t msg_len, bool is_binary, bool compress);
size_t xyra_ws_get_remote_address_bytes(xyra_websocket_t* ws, const char** out_addr);

#ifdef __cplusplus
}
#endif

#endif // XYRA_C_API_H