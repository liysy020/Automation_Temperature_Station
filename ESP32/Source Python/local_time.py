import time
from lib import ntptime

class local_time:
    def __init__(self, offset=0, dls_start=None, dls_end=None):
        self.Time_Offset = offset
        self.DLS_Start_Month, self.DLS_Start_Day = dls_start if dls_start else (0, 0)
        self.DLS_End_Month, self.DLS_End_Day = dls_end if dls_end else (0, 0)
        self.synced = False
        self.sync_time() #inital system time to sync with Internet

    def sync_time(self):
        if not self.synced:
            try:
                ntptime.settime()
                self.synced = True
            except Exception as e:
                print("NTP sync failed:", e)
                self.synced = False
    
    def is_dst(self, t):
        year = t[0]
        month = t[1]
        day = t[2]
        weekday = t[6]

        # DST starts
        if month == self.DLS_Start_Month:
            first_day = self.DLS_Start_Day - (time.mktime((year, 10, 1, 0, 0, 0, 0, 0)) % 7)
            if day >= first_day:
                return True
            else:
                return False
        # DST ends
        elif month == self.DLS_End_Month:
            first_sunday = self.DLS_End_Day - (time.mktime((year, 4, 1, 0, 0, 0, 0, 0)) % 7)
            if day < first_sunday:
                return True
            else:
                return False
        elif month > self.DLS_Start_Month or month < self.DLS_End_Month:
            return True
        else:
            return False

    def get_time(self):
        if not self.synced:
            self.sync_time()
        try:
            t = time.localtime()
            # offset for timezone
            offset = self.Time_Offset * 3600
            # offset for Day Light Saving
            if self.DLS_Start_Month !=0 and self.DLS_End_Month !=0:
                if self.is_dst(t):
                    offset += 3600  # Add 1 hour for DST

            local_time = time.localtime(time.mktime(t) + offset)
            return local_time
        except Exception as e:
            print('Failed to get system time due to time sync issue')
            return None

    def get_display_time(self):
        MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        t= self.get_time()
        if not t:
            return 'Time Error'
        hour = t[3]
        minute = t[4]
        day = t[2]
        month_index = t[1] - 1
        month_abbr = MONTHS[month_index] if 0 <= month_index < 12 else '???'
        time_str = "{:02d}:{:02d}  {:02d} {}".format(hour, minute, day, month_abbr)
        return time_str
