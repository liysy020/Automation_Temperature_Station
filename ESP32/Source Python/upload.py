import usocket as socket
import ssl
import json


def https_post(host, port, path, headers, data):
    addr_info = socket.getaddrinfo(host, port)[0][-1]
    sock = socket.socket()
    sock.connect(addr_info)
    sock = ssl.wrap_socket(sock, server_hostname=host)

    payload = json.dumps(data)
    payload_bytes = payload.encode('utf-8')
    header_lines = [
        f"Host: {host}",
        "Content-Type: application/json",
        "Connection: close",
    ]
    for k, v in headers.items():
        header_lines.append(f"{k}: {v}")
    header_lines.append(f"Content-Length: {len(payload_bytes)}")
    header_lines.append("")  # blank line
    request_lines = [
        f"POST {path} HTTP/1.1",
    ] + header_lines + [
       ""  # blank line separating headers and body
    ]
    request = "\r\n".join(request_lines).encode('utf-8') + payload_bytes
    sock.write(request)
    sock.close()

def send (host, port, path, DEVICE_NAME, API_KEY, temp):
    data = {
        "temperature": temp
    }
    headers = {
        "Device-Name": DEVICE_NAME,
        "Api-Key": API_KEY
    }
    https_post(host, port, path, headers, data)

