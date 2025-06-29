import network
import time
from upload import send
from local_time import local_time
from display_LCD1602 import LCD_Display
from sensor_DS18B20 import sensor
#Wifi detail
SSID = 'Express'
PASSWORD = 'enoZsserpxE'
#server deatil
host = '10.1.1.9'
DEVICE_NAME = 'test_sensor'
API_KEY = '7b0dfe2abd683316672c33c89b7ecf234a13f53632f3c0aa1ac656c7e5956a30'
port = 8000
path = "/api/temperature/"

#Day Light Saving setting
DLS_Start_Month = 10 #Oct
DLS_Start_Day = 7 #Sunday
DLS_End_Month = 4 #Apr
DLS_End_Day = 7 #Synday
#Timezone Offset
TZ_Offset = 10 #Sydney/Australia

#LCD Display PIN number
SDA_PIN = 21
SCL_PIN = 22
#Temperature Sensor PIN number
TEMP_PIN = 2

# Wi-Fi function
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)

#connect to Wifi
connect_wifi()
#setup local time to system clock
localtime = local_time(offset=TZ_Offset, dls_start=(DLS_Start_Month,DLS_Start_Day), dls_end=(DLS_End_Month,DLS_End_Day))
#Initial LCD display module LCD1602
LCD = LCD_Display(SDA_PIN,SCL_PIN)
#Inital temperature sensor DS18B20
temp_sensor = sensor(TEMP_PIN)

while_loop_counter = 0 #data will send to server every 2 mins while display refresh every 10 sec
while True:
    time_string = localtime.get_display_time()
    hour = localtime.get_time()[3]
    temp= temp_sensor.read()
    if 22 <= hour or hour < 6: #Switch off the backlight between 10pm to 6am
        LCD.display(time_string, "Temp:  "+str(temp), False)
    else:
        LCD.display(time_string, "Temp:  "+str(temp), True)
    try:
        while_loop_counter += 1
        if while_loop_counter == 12:
            send (host, port, path, DEVICE_NAME, API_KEY, temp)
            while_loop_counter = 0
    except Exception as e:
        print (str(e))
        pass
    time.sleep(10)