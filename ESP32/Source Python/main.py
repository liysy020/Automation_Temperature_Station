import network, time, json
from upload import send
from local_time import local_time
from display_LCD1602 import LCD_Display
import sensors

#Day Light Saving setting
DLS_Start_Month = 10 #Oct
DLS_Start_Day = 7 #Sunday
DLS_End_Month = 4 #Apr
DLS_End_Day = 7 #Synday
#Timezone Offset
TZ_Offset = 10 #Sydney/Australia
#setup local time to system clock
localtime = local_time(offset=TZ_Offset, dls_start=(DLS_Start_Month,DLS_Start_Day), dls_end=(DLS_End_Month,DLS_End_Day))


#LCD Display PIN number
SDA_PIN = 21
SCL_PIN = 22
#Initial LCD display module LCD1602
LCD = LCD_Display(SDA_PIN,SCL_PIN)

#Temperature Sensor PIN number
TEMP_PIN = 2
#Inital temperature sensor DS18B20
SENSOR_READY = False


#setup server detail
CONFIG_FILE = "initial.conf"
host = ''
DEVICE_NAME = ''
API_KEY = ''
port = 443
path = "/api/temperature/"
HOST_READY = False
try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        if not config:
            HOST_READY = False
        else:
            host = config.get("server")
            DEVICE_NAME = config.get("api_name")
            API_KEY = config.get("api_key")
            HOST_READY = True
except Exception as e:
    print ('set up server detail error:'+ str(e))
    HOST_READY = False

#setup sensor type by sending temp=0 and hum=0 to the server
#sever will respond with value of sensor-type
try:
    if not HOST_READY:
        SENSOR_READY = False
    else:
        respond = send (host=host, port=port, path=path, DEVICE_NAME=DEVICE_NAME, API_KEY=API_KEY)
        parts = respond.split(b'\r\n\r\n', 1)
        if len(parts) < 2:
            print("Invalid HTTP response: no body found")
        else:
            body_bytes = parts[1]
            body_str = body_bytes.decode('utf-8')
            body_json = json.loads(body_str)
            
            if 'Temperature' in body_json.get("sensor-type"):
                sensor = sensors.sensor_ds18x20(TEMP_PIN)
            SENSOR_READY = True
except Exception as e:
    print ('Failed to setup sensor type or server is not available'+str(e))
    SENSOR_READY = False

while_loop_counter = 12 #data will send to server every 2 mins while display refresh every 10 sec
while True:
    try:
        while_loop_counter = while_loop_counter -1
        str_temp = ''
        temp = 0
        humi = 0
        if SENSOR_READY:
            temp = sensor.read()
            str_temp= str(temp)
        time_string = localtime.get_display_time()
        t = localtime.get_time()
        if t:
            hour = t[3]
            if hour >= 22 or hour < 6: #Switch off the backlight between 10pm to 6am
                LCD.display(time_string, "Temp:  "+str_temp, False)
            else:
                LCD.display(time_string, "Temp:  "+str_temp, True)
        if while_loop_counter <= 0 and HOST_READY:
            send (host=host, port=port, path=path, DEVICE_NAME=DEVICE_NAME, API_KEY=API_KEY, temp=temp, humi=humi)
            while_loop_counter = 12 # reset the counter
            print('Data sent to server')
    except Exception as e:
        print (str(e))
        continue
    time.sleep(10)