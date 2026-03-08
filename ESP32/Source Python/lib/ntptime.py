import usocket
import ustruct
import utime
import machine

NTP_DELTA = 2208988800  # Seconds between 1900 and 1970
Y2K_OFFSET = 946684800  # Seconds between 1970 and 2000
NTP_HOST = "pool.ntp.org"

def time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B  # NTP request header
    addr = usocket.getaddrinfo(NTP_HOST, 123)[0][-1]
    s = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
    try:
        s.settimeout(1)
        s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()
    # Extract NTP seconds (since 1900)
    val = ustruct.unpack("!I", msg[40:44])[0]
    ntp_seconds = val & 0xFFFFFFFF
    
    # Convert from NTP (1900) to Unix (1970) to local epoch (2000)
    # Your MicroPython port uses 2000-01-01 as epoch
    seconds_since_2000 = ntp_seconds - NTP_DELTA - Y2K_OFFSET
    return seconds_since_2000
def settime():
    t = time()
    tm = utime.gmtime(t)
    machine.RTC().datetime((
        tm[0], tm[1], tm[2], tm[6]+1,  # year, month, day, weekday (Mon=1)
        tm[3], tm[4], tm[5], 0          # hour, min, sec, subsecs
    ))