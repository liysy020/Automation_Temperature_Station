import socket
import machine
import json


CONFIG_FILE = "initial.conf"

html = """<!DOCTYPE html>
<html>
  <head><title>Device Setup</title></head>
  <body>
    <h1>Configure WiFi & Server</h1>
    <form method="POST">
      SSID: <input name="ssid"><br>
      Password: <input name="password" type="password"><br><br>
      
      Server Address: <input name="server"><br>
      API Name: <input name="api_name"><br>
      API Key: <input name="api_key"><br><br>

      <button type="submit">Save and Reboot</button>
    </form>
  </body>
</html>
"""
def url_decode(s):
    res = ''
    i = 0
    while i < len(s):
        c = s[i]
        if c == '+':
            res += ' '
        elif c == '%':
            hex_value = s[i+1:i+3]
            res += chr(int(hex_value, 16))
            i += 2
        else:
            res += c
        i += 1
    return res

def parse_form(data):
    # decode form data
    params = {}
    for pair in data.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            params[url_decode(key)] = url_decode(value)
    return params

def save_config(new_config):
    # Load existing config if it exists
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except:
        config = {}

    # Update only non-empty fields
    for key, value in new_config.items():
        if value.strip():  # Only overwrite if not empty after stripping spaces
            config[key] = value

    # Save merged config back to file
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def start_web_server():
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print("Web server running at http://192.168.0.1/")

    while True:
        conn, addr = s.accept()
        print("Client connected from", addr)
        request = conn.recv(1024).decode()

        if "POST" in request:
            body = request.split("\r\n\r\n", 1)[1]
            form = parse_form(body)
            save_config(form)

            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
            response += "<h1>Configuration Saved. Rebooting...</h1>"
            conn.send(response)
            conn.close()
            machine.reset()
        else:
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html
            conn.send(response)
            conn.close()

start_web_server()
