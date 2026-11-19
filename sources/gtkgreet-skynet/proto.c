#define _POSIX_C_SOURCE 200809L

#include <json-c/json_object.h>
#include <json-c/json_tokener.h>

#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <stdint.h>
#include <string.h>

#include "proto.h"

/* Requests are small, fixed-size protocol structures. Encode them directly
 * into one bounded buffer: JSON-C must never own a second password copy. */
#define REQUEST_CAPACITY (6 * sizeof(((struct request *)0)->body) + 128)
#define MAX_RESPONSE_BYTES (1024 * 1024)

static void clear_bytes(void *memory, size_t length) {
    volatile unsigned char *p = memory;
    while (length--) *p++ = 0;
}

void clear_request(struct request *req) {
    clear_bytes(req, sizeof(*req));
}

static int encode_request(const struct request *req, char *out, size_t capacity) {
    const char *prefix, *suffix = "}", *value = NULL;
    size_t value_capacity = 0;
    switch (req->request_type) {
        case request_type_create_session:
            prefix = "{\"type\":\"create_session\",\"username\":";
            value = req->body.request_create_session.username;
            value_capacity = sizeof(req->body.request_create_session.username);
            break;
        case request_type_start_session:
            prefix = "{\"type\":\"start_session\",\"cmd\":[";
            suffix = "]}";
            value = req->body.request_start_session.cmd;
            value_capacity = sizeof(req->body.request_start_session.cmd);
            break;
        case request_type_post_auth_message_response:
            prefix = "{\"type\":\"post_auth_message_response\",\"response\":";
            value = req->body.request_post_auth_message_response.response;
            value_capacity = sizeof(req->body.request_post_auth_message_response.response);
            break;
        case request_type_cancel_session:
            prefix = "{\"type\":\"cancel_session\"";
            break;
        default:
            return -1;
    }
    size_t used = strlen(prefix);
    if (used >= capacity) return -1;
    memcpy(out, prefix, used);
    if (value) {
        size_t length = strnlen(value, value_capacity);
        if (length == value_capacity || used + 2 >= capacity) return -1;
        out[used++] = '"';
        for (size_t i = 0; i < length; ++i) {
            unsigned char c = (unsigned char)value[i];
            if (used + 6 + 2 + strlen(suffix) >= capacity) return -1;
            if (c == '"' || c == '\\') {
                out[used++] = '\\';
                out[used++] = (char)c;
            } else if (c < 0x20) {
                static const char hex[] = "0123456789abcdef";
                memcpy(out + used, "\\u00", 4);
                used += 4;
                out[used++] = hex[c >> 4];
                out[used++] = hex[c & 15];
            } else {
                out[used++] = (char)c;
            }
        }
        out[used++] = '"';
    }
    size_t tail = strlen(suffix);
    if (used + tail >= capacity) return -1;
    memcpy(out + used, suffix, tail + 1);
    return (int)(used + tail);
}

static int send_all(int fd, const void *buffer, size_t length) {
    const char *bytes = buffer;
    size_t off = 0;
    while (off < length) {
        ssize_t n = send(fd, bytes + off, length - off, MSG_NOSIGNAL);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return -1;
        off += (size_t)n;
    }
    return 0;
}

static int write_req(int fd, const char *payload, uint32_t length) {
    if (send_all(fd, &length, sizeof(length)) < 0) return -1;
    return send_all(fd, payload, length);
}

static struct json_object* read_resp(int fd) {
    struct json_object* resp = NULL;
    char *respstr = NULL;
    uint32_t len;
    uint32_t off = 0;

    while (off < 4) {
        char* headerp = (char*)&len;
        ssize_t n = read(fd, &headerp[off], 4-off);
        if (n < 0 && errno == EINTR) continue;
        if (n < 1) {
            goto end;
        }
        off += n;
    }

    off = 0;
    if (len == 0 || len > MAX_RESPONSE_BYTES) goto end;
    respstr = (char*)calloc(1, (size_t)len + 1);
    if (respstr == NULL) goto end;
    while (off <len) {
        int n = read(fd, &respstr[off],len-off);
        if (n < 0 && errno == EINTR) continue;
        if (n < 1) {
            goto end;
        }
        off += n;
    }

    resp = json_tokener_parse(respstr);

end:
    if (respstr != NULL) {
        free(respstr);
    }
    return resp;
}

static int connectto(const char* path) {
    if (strlen(path) >= sizeof(((struct sockaddr_un *)0)->sun_path)) {
        errno = ENAMETOOLONG;
        return -1;
    }
    int fd = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
    if (fd < 0) {
        fprintf(stderr, "unable to open socket\n");
        return -1;
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strcpy(addr.sun_path, path);
    if (connect(fd, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
        fprintf(stderr, "connect: error: %d\n", errno);
        close(fd);
        return -1;
    }

    return fd;
}

static struct json_object* roundtrip_json(char *payload, uint32_t length, size_t capacity) {
    struct json_object* resp = NULL;
    int fd = -1;
    char* greetd_sock = getenv("GREETD_SOCK");

    if (greetd_sock == NULL) {
        fprintf(stderr, "GREETD_SOCK not set\n");
        goto end;
    }

    if ((fd = connectto(greetd_sock)) < 0) {
        fprintf(stderr, "unable to connect to socket\n");
        goto end;
    }

    int written = write_req(fd, payload, length);
    /* Erase even while the daemon may be waiting for a fingerprint/reply. */
    clear_bytes(payload, capacity);
    if (written != 0) {
        fprintf(stderr, "unable to write request to socket\n");
        goto end;
    }

    if ((resp = read_resp(fd)) == NULL) {
        fprintf(stderr, "unable to read response from socket\n");
        goto end;
    }

end:
    clear_bytes(payload, capacity);
    if (fd >= 0) {
        close(fd);
    }
    return resp;
}

const char* json_get_string_from_object(struct json_object* obj, const char* key) {

    struct json_object* val = json_object_object_get(obj, key);
    if (val == NULL || !json_object_is_type(val, json_type_string)) {
        return NULL;
    }
    return json_object_get_string(val);
}

struct response roundtrip(struct request *req) {
    char payload[REQUEST_CAPACITY] = {0};
    int length = encode_request(req, payload, sizeof(payload));
    clear_request(req);
    struct response resp = {
        .response_type = response_type_roundtrip_error,
    };
    resp.body.response_error.error_type = error_type_error;

    struct json_object* json_resp = NULL;
    if (length >= 0)
        json_resp = roundtrip_json(payload, (uint32_t)length, sizeof(payload));
    clear_bytes(payload, sizeof(payload));
    if (json_resp == NULL) {
        snprintf(resp.body.response_error.description, 128, "proto: roundtrip failed");
        goto done;
    }

    if (!json_object_is_type(json_resp, json_type_object)) {
        snprintf(resp.body.response_error.description, 128, "proto: expected object");
        goto done;
    }
    const char* typestr = json_get_string_from_object(json_resp, "type");
    if (typestr == NULL) {
        snprintf(resp.body.response_error.description, 128, "proto: no type found");
        goto done;
    }


    if (strcmp(typestr, "success") == 0) {
        resp.response_type = response_type_success;
        goto done;
    }

    if (strcmp(typestr, "auth_message") == 0) {
        const char* messagestr = json_get_string_from_object(json_resp, "auth_message");
        if (messagestr == NULL) {
            resp.response_type = response_type_error;
            snprintf(resp.body.response_error.description, 128, "proto: no message");
            goto done;
        }
        const char* auth_message_typestr = json_get_string_from_object(json_resp, "auth_message_type");
        if (auth_message_typestr == NULL) {
            resp.response_type = response_type_error;
            snprintf(resp.body.response_error.description, 128, "proto: no message type");
            goto done;
        }
        resp.response_type = response_type_auth_message;
        if (strcmp(auth_message_typestr, "visible") == 0) {
            resp.body.response_auth_message.auth_message_type = auth_message_type_visible;
        } else if (strcmp(auth_message_typestr, "secret") == 0) {
            resp.body.response_auth_message.auth_message_type = auth_message_type_secret;
        } else if (strcmp(auth_message_typestr, "info") == 0) {
            resp.body.response_auth_message.auth_message_type = auth_message_type_info;
        } else if (strcmp(auth_message_typestr, "error") == 0) {
            resp.body.response_auth_message.auth_message_type = auth_message_type_error;
        } else {
            resp.response_type = response_type_error;
            snprintf(resp.body.response_error.description, 128, "proto: unknown message type");
            goto done;
        }

        strncpy(resp.body.response_auth_message.auth_message, messagestr, sizeof(resp.body.response_auth_message.auth_message)-1);
        goto done;
    }

    if (strcmp(typestr, "error") == 0) {
        const char* descriptionstr = json_get_string_from_object(json_resp, "description");
        if (descriptionstr == NULL) {
            resp.response_type = response_type_error;
            snprintf(resp.body.response_error.description, 128, "proto: no error description");
            goto done;
        }
        resp.response_type = response_type_error;

        const char* errortypestr = json_get_string_from_object(json_resp, "error_type");
        if (errortypestr == NULL) {
            snprintf(resp.body.response_error.description, 128, "proto: no error type");
            goto done;
        }
        if (strcmp(errortypestr, "auth_error") == 0) {
            resp.body.response_error.error_type = error_type_auth;
        } else {
            resp.body.response_error.error_type = error_type_error;
        }

        strncpy(resp.body.response_error.description, descriptionstr, sizeof(resp.body.response_error.description)-1);
        goto done;
    }

    snprintf(resp.body.response_error.description, 128, "proto: no known type");

done:
    json_object_put(json_resp);
    return resp;
}
