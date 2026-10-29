# f-api-12: two requests on ONE socket to a server on 127.0.0.1:<port>; print what comes back for each.
# usage: python3 raw-keepalive.py <port> <path> [get|soap]
import socket, sys, time
port, path, kind = int(sys.argv[1]), sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "get")
body = (b'<?xml version="1.0"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        b'<soap:Body><Add><a>1</a><b>10</b></Add></soap:Body></soap:Envelope>')
def req():
    if kind == "get":
        return f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: Keep-Alive\r\n\r\n".encode()
    return (f"POST {path} HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: Keep-Alive\r\nContent-Type: text/xml; charset=utf-8\r\n"
            f"SOAPAction: \"Add\"\r\nContent-Length: {len(body)}\r\n\r\n").encode() + body
s = socket.create_connection(("127.0.0.1", port)); s.settimeout(3)
for n in (1, 2):
    s.sendall(req()); buf = b""; t = time.time()
    while True:
        try: c = s.recv(65536)
        except socket.timeout: print(f"req {n}: TIMEOUT after {time.time()-t:.1f}s, got {len(buf)} bytes"); break
        if not c: print(f"req {n}: CONNECTION CLOSED by server after {len(buf)} bytes"); break
        buf += c
        if b"\r\n\r\n" in buf:
            h, _, b = buf.partition(b"\r\n\r\n"); cl = [l for l in h.split(b"\r\n") if l.lower().startswith(b"content-length:")]
            if cl and len(b) >= int(cl[0].split(b":")[1]): break
    head = buf.split(b"\r\n\r\n")[0].decode(errors="replace").split("\r\n")
    print(f"req {n}: {head[0] if head else '-'} | " + " | ".join(l for l in head if l.lower().startswith(("connection", "content-length"))))
