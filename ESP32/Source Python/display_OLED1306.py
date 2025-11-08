from machine import I2C, Pin
from lib import ssd1306, big_font

class OLED_Display:
    def __init__(self, sda_pin, scl_pin, width=128, height=32):
        try:
            self.i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=100_000)
            self.lcd = ssd1306.SSD1306_I2C(width, height, self.i2c)
        except Exception as e:
            print("Invalid SDA or SCL pin:", e)
            self.lcd = None
    
    def display(self, line1=None, line2=None, line3=None, line4=None, temp=None, humi=None):
        if not self.lcd:
            return
        self.lcd.fill(0)
        if temp or humi:                
            self.bf = big_font.BigFont
            if temp:
                x = 0
                for c in temp:
                    self.bf.draw(self.lcd, c, x, 0)
                    x += 16  # move right for next digit
                self.bf.draw(self.lcd, '°', x, 0)
                x += 16
                self.bf.draw(self.lcd, 'C', x, 0)
                x += 16
                self.bf.draw(self.lcd, ' ', x, 0)
                x += 16
            if humi:
                for c in humi:
                    self.bf.draw(self.lcd, c, x, 0)
                    x += 16
                self.bf.draw(self.lcd, '%', x, 0)
        else:
            if line1:
                self.lcd.text (line1, 0, 0)
            if line2:
                self.lcd.text (line2, 0, 8)
            if line3:
                self.lcd.text (line3, 0, 16)
            if line4:
                self.lcd.text (line4, 0, 32)
        self.lcd.show()
        
    
                    

