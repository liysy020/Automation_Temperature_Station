import machine
import time
import network
import json
import os

CONFIG_FILE = "initial.conf"

def read_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def connect_to_wifi():
    config = read_config()
    if not config:
        return False

    ssid = config.get("ssid")
    password = config.get("password")
    try:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(ssid, password)
    except:
        return False

    for _ in range(20):
        if wlan.isconnected():
            print("Connected to WiFi:", wlan.ifconfig())
            return True
        time.sleep(1)

    print("WiFi connection failed.")
    return False

def start_ap_mode():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.ifconfig(('192.168.0.1', '255.255.255.0', '192.168.0.1', '8.8.8.8'))
    ap.config(essid='set_me_up', password='password', authmode=network.AUTH_WPA_WPA2_PSK)
    print("Started AP Mode at 192.168.0.1")


if connect_to_wifi():
    print("Wi-Fi connected. Skipping AP mode and web server.")
else:
    start_ap_mode()
    print("Waiting for AP to stabilize...")
    time.sleep(3)
    print("Starting web server...")
    import websetup
