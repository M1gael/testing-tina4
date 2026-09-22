/* Stand-in language server for tina4 serve on Windows.
 * Inherits the CLI process environment, then:
 *   INHERIT: getenv("TINA4_CSP") written to dump.txt
 *   WIRE:    HTTP Content-Security-Policy — getenv if set, else .env
 *            (same first-wins rule as Tina4\DotEnv)
 * Listens on PORT (set by tina4 serve). */
#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void unquote_one_pair(char *v) {
    size_t n = strlen(v);
    while (n && (v[0] == ' ' || v[0] == '\t')) { memmove(v, v + 1, n); n--; }
    while (n && (v[n - 1] == ' ' || v[n - 1] == '\t' || v[n - 1] == '\r')) {
        v[--n] = 0;
    }
    if (n >= 2 && (v[0] == '"' || v[0] == '\'') && v[n - 1] == v[0]) {
        v[n - 1] = 0;
        memmove(v, v + 1, n - 1);
    }
}

static int read_env_key(const char *key, char *out, size_t cap) {
    FILE *f = fopen(".env", "rb");
    char line[4096];
    if (!f) return 0;
    while (fgets(line, sizeof line, f)) {
        char *nl = strchr(line, '\n');
        if (nl) *nl = 0;
        char *cr = strchr(line, '\r');
        if (cr) *cr = 0;
        char *eq = strchr(line, '=');
        if (!eq) continue;
        *eq = 0;
        char *k = line;
        while (*k == ' ' || *k == '\t') k++;
        if (strcmp(k, key) != 0) continue;
        strncpy(out, eq + 1, cap - 1);
        out[cap - 1] = 0;
        unquote_one_pair(out);
        fclose(f);
        return 1;
    }
    fclose(f);
    return 0;
}

int main(void) {
    const char *port_s = getenv("PORT");
    if (!port_s) port_s = "7145";
    int port = atoi(port_s);

    const char *inherited = getenv("TINA4_CSP");
    FILE *dump = fopen("dump.txt", "w");
    if (dump) {
        fprintf(dump, "TINA4_CSP=%s\n", inherited ? inherited : "<unset>");
        fclose(dump);
    }

    char file_val[4096];
    const char *wire = inherited;
    if (!wire && read_env_key("TINA4_CSP", file_val, sizeof file_val)) {
        wire = file_val;
    }
    if (!wire) wire = "<unset>";

    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return 2;
    SOCKET s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (s == INVALID_SOCKET) return 3;
    BOOL reuse = 1;
    setsockopt(s, SOL_SOCKET, SO_REUSEADDR, (char *)&reuse, sizeof reuse);
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = htons((u_short)port);
    if (bind(s, (struct sockaddr *)&addr, sizeof addr) != 0) return 4;
    if (listen(s, 4) != 0) return 5;

    for (;;) {
        SOCKET c = accept(s, NULL, NULL);
        if (c == INVALID_SOCKET) break;
        char req[1024];
        recv(c, req, sizeof req, 0);
        char body[] = "ok";
        char hdr[4600];
        int n = snprintf(hdr, sizeof hdr,
            "HTTP/1.1 200 OK\r\n"
            "Content-Security-Policy: %s\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 2\r\n"
            "Connection: close\r\n"
            "\r\n"
            "%s",
            wire, body);
        send(c, hdr, n, 0);
        closesocket(c);
    }
    closesocket(s);
    WSACleanup();
    return 0;
}
