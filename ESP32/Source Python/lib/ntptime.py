import usocket
import ustruct
import utime
import machine

NTP_DELTA = 2208988800  # Seconds between 1900 and 1970
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
    val = ustruct.unpack("!I", msg[40:44])[0]
    return val - NTP_DELTA

def settime():
    t = time()
    tm = utime.localtime(t)
    machine.RTC().datetime((
        tm[0], tm[1], tm[2], tm[6] + 1,  # year, month, day, weekday (Mon=1)
        tm[3], tm[4], tm[5], 0          # hour, min, sec, subsecs
    ))
