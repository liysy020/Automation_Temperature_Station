import network, time, json
from upload import send
from local_time import local_time
from display_OLED1306 import OLED_128x32
from display_OLED1306 import OLED_128x64
from display_LCD1602 import LCD_Display
import sensors
from machine import Pin
##################### define attributes #########################
#Day Light Saving setting
DLS_Start_Month = 10 #Oct
DLS_Start_Day = 7 #Sunday
DLS_End_Month = 4 #Apr
DLS_End_Day = 7 #Synday
#Timezone Offset
TZ_Offset = 10 #Sydney/Australia
#setup local time to system clock
localtime = local_time(offset=TZ_Offset, dls_start=(DLS_Start_Month,DLS_Start_Day), dls_end=(DLS_End_Month,DLS_End_Day))

#Select one of the below display models
#Display PIN number
SDA_PIN = 0
SCL_PIN = 0
# Initial LCD display module LCD1602
#LCD = LCD_Display(SDA_PIN,SCL_PIN) if SDA_PIN != 0 and SCL_PIN != 0 else None

# Initial OLED display module 128x32
#LCD = OLED_128x32(SDA_PIN,SCL_PIN) if SDA_PIN != 0 and SCL_PIN != 0 else None

# Initial OLED display module 128x64
LCD = OLED_128x64(SDA_PIN,SCL_PIN) if SDA_PIN != 0 and SCL_PIN != 0 else None

#Temperature Sensor PIN number
TEMP_PIN = 0
# When the sensor placed too close to ESP chip
TEMP_OFFSET = 0
HUMI_OFFSET = 0
#Initalize temperature sensor
SENSOR_READY = False

# PLC application PIN. Set to 0 will disable power trigging function
# The PIN number that connected to an application. It will be power on when low temperature triggered
SW1_PIN = 0
switch1 = Pin(SW1_PIN, Pin.OUT) if SW1_PIN !=0 else None
# The PIN number that connected to an application. It will be power on when high temperature triggered
SW2_PIN = 0
switch2 = Pin(SW2_PIN, Pin.OUT) if SW2_PIN !=0 else None
# The PIN number that connected to an application. It will be power on when low humidity triggered
SW3_PIN = 0
switch3 = Pin(SW3_PIN, Pin.OUT) if SW3_PIN !=0 else None
# The PIN number that connected to an application. It will be power on when high humidity triggered
SW4_PIN = 0
switch4 = Pin(SW4_PIN, Pin.OUT) if SW4_PIN !=0 else None
# Application trigger condtion. Value will be assign by initiating connection to server 
T_Low = None
T_High = None
H_Low = None
H_High = None

#setup server detail
CONFIG_FILE = "initial.conf"
host = ''
DEVICE_NAME = ''
API_KEY = ''
port = 443
path = "/api/temperature/"
HOST_READY = False

#switch screen off at midnight. hours define in below. 0 means always_on
NIGHT_TIME_START = 0
NIGHT_TIME_FINISH = 0

########################## prgram start ################################
def is_night (t):
    hour = t[3]
    if NIGHT_TIME_START == 0 and NIGHT_TIME_FINISH == 0:
        return False
    if hour >= NIGHT_TIME_START or hour < NIGHT_TIME_FINISH:
        return True
    return False

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
#server will respond with value of sensor-type and PLC power trigger value
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
            
            if TEMP_PIN == 0:
                SENSOR_READY = False
            else:
                if 'Temperature' in body_json.get("sensor-type"):
                    sensor = sensors.sensor_ds18x20(TEMP_PIN)
                elif 'Humidity' in body_json.get("sensor-type") and 'DHT11' in body_json.get("sensor-type"):
                    sensor = sensors.sensor_dht11(TEMP_PIN)
                elif 'Humidity' in body_json.get("sensor-type") and 'DHT22' in body_json.get("sensor-type"):
                    sensor = sensors.sensor_dht22(TEMP_PIN)
                SENSOR_READY = True

            T_Low = body_json.get("T_Low")
            T_High = body_json.get("T_High")
            H_Low = body_json.get("H_Low")
            H_High = body_json.get("H_High")
            
            if T_Low == 0 and T_High == 0:
                T_Low = None
                T_High = None
            if H_Low == 0 and H_High == 0:
                H_Low = None
                H_High = None
except Exception as e:
    print ('Failed to setup sensor type or server is not available '+str(e))
    SENSOR_READY = False

# print out device status:
if not LCD:
    print ('LCD is not configured!')
if not SENSOR_READY:
    print ('Sensor is not ready')
    
while_loop_counter = 12 #data will send to server every 2 mins while display refresh every 10 sec
while True:
    try:
        while_loop_counter = while_loop_counter -1
        str_temp = ''
        str_humi = ''
        temp = 0
        humi = 0
        if SENSOR_READY: # read sensor information
            data = sensor.read()
            print('senor readings: ' + str(data))
            try:
                if data:
                    temp, humi = data
                    temp = temp - TEMP_OFFSET
                    humi = humi - HUMI_OFFSET
            except:
                if data:
                    temp = data - TEMP_OFFSET
            str_temp = str(temp)
            str_humi = str(humi)
            if switch1 and T_Low:
                if temp <= float(T_Low): # Low temperature alert triggers switch 1 to power on
                    switch1.value(1)
                    print ('Low temperature trigger switch1 to power on')
                else:
                    switch1.value(0)
                    print ('switch 1 power off')
            if switch2 and T_High:
                if temp >= float(T_High): # High temperature alert trigger switch 2 to power on
                    switch2.value(1)
                    print ('High temperature trigger switch2 to power on')
                else:
                    switch2.value(0)
                    print ('switch 2 power off')
            if switch3 and H_Low:
                if humi <= float(H_Low): # Low Humidity alert trigger switch 3 to power on
                    switch3.value(1)
                    print ('Low Humidity trigger switch3 to power on')
                else:
                    switch3.value(0)
                    print ('switch 3 power off')
            if switch4 and H_High:
                if humi >= float(H_High): # High Humidity alert trigger switch4 to power on
                    switch4.value(1)
                    print ('High Humidity trigger switch4 to power on')
                else:
                    switch4.value(0)
                    print ('swtich 4 power off')
                
        time_string = localtime.get_display_time()
        t = localtime.get_time()
        if LCD:
            if (isinstance (LCD, OLED_128x32) or isinstance (LCD, OLED_128x64)) and t and LCD.lcd !=None: # for OLED display to print in big font
                if is_night (t): #Switch screen off by display white space
                    if isinstance (LCD, OLED_128x32):
                        LCD.display (line1 = ' ', line2 = ' ')
                    elif isinstance (LCD, OLED_128x64):
                        LCD.display (line1 = ' ', line2 = ' ', line3 = ' ', line4 = ' ')
                else:
                    if str_humi == '0': #temperture sensor
                        LCD.display (temp = str(int(temp)))
                    else: # temperture and humidity combined sensor
                        LCD.display (temp = str(int(temp)), humi = str(int(humi)))
            elif isinstance (LCD, LCD_Display) and t and LCD.lcd != None: # LCD display print datetime and temp/humi
                if is_night (t): #Switch off the backlight with display at the backgroup
                    if str_humi == '0':
                        LCD.display(line1 = time_string, line2 = "Temp:  "+str_temp+"C", backlight = False)
                    else:
                        LCD.display(line1 = time_string, line2 = "T:"+str_temp+"C H:"+str_humi+"%", backlight = False)
                else:
                    if str_humi == '0':
                        LCD.display(line1 = time_string, line2 = "Temp:  "+str_temp+ "°C")
                    else:
                        LCD.display(line1 = time_string, line2 = "T:"+str_temp+"°C H:"+str_humi+"%")
        if while_loop_counter <= 0 and HOST_READY and SENSOR_READY: # server is connected 
            while_loop_counter = 12 # reset the counter
            print('Data sent to server')
            send (host=host, port=port, path=path, DEVICE_NAME=DEVICE_NAME, API_KEY=API_KEY, temp=temp, humi=humi)                
    except Exception as e:
        print (str(e))
        continue
    time.sleep(10)