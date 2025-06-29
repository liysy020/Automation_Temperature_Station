from machine import I2C, Pin
from lib.lcd_api import LcdApi
from lib.i2c_lcd import I2cLcd

class LCD_Display:
    def __init__(self, sda_pin, scl_pin):
        self.i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=400000)
        self.lcd = I2cLcd(self.i2c, 0x27, 2, 16)
        
    def display(self, line1, line2):
        #display row 1
        self.lcd.move_to(0, 0)
        self.lcd.putstr (line1)
        #display row 2
        self.lcd.move_to(0, 1)
        self.lcd.putstr (line2)

