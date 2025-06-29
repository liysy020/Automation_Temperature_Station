from lcd_api import LcdApi
from machine import I2C
import time

class I2cLcd(LcdApi):
    # Commands
    LCD_I2C_ADDR = 0x27
    LCD_WIDTH = 16
    LCD_CHR = 1
    LCD_CMD = 0
    LCD_BACKLIGHT = 0x08

    ENABLE = 0b00000100

    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.num_lines = num_lines
        self.num_columns = num_columns
        self.backlight = self.LCD_BACKLIGHT
        
        super().__init__(num_lines, num_columns)
        
        self._write_byte(0)
        time.sleep_ms(20)

        self.hal_write_init_nibble(0x03)
        time.sleep_ms(5)
        self.hal_write_init_nibble(0x03)
        time.sleep_ms(1)
        self.hal_write_init_nibble(0x03)
        self.hal_write_init_nibble(0x02)

        self.hal_write_command(self.LCD_FUNCTION | self.LCD_FUNCTION_2LINES)
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)
        self.hal_write_command(self.LCD_CLR)
        self.hal_write_command(self.LCD_ENTRY_MODE | self.LCD_ENTRY_INC)

    def hal_write_init_nibble(self, nibble):
        byte = (nibble << 4) | self.backlight
        self._write_byte(byte)
        self._strobe(byte)

    def hal_backlight_on(self):
        self.backlight = self.LCD_BACKLIGHT
        self._write_byte(0)

    def hal_backlight_off(self):
        self.backlight = 0x00
        self._write_byte(0)

    def hal_write_command(self, cmd):
        self._write_byte_mode(cmd, self.LCD_CMD)

    def hal_write_data(self, data):
        self._write_byte_mode(data, self.LCD_CHR)

    def _write_byte_mode(self, bits, mode):
        high = mode | (bits & 0xF0) | self.backlight
        low = mode | ((bits << 4) & 0xF0) | self.backlight
        self._write_byte(high)
        self._strobe(high)
        self._write_byte(low)
        self._strobe(low)

    def _strobe(self, data):
        self._write_byte(data | self.ENABLE)
        time.sleep_us(500)
        self._write_byte(data & ~self.ENABLE)
        time.sleep_us(100)

    def _write_byte(self, data):
        self.i2c.writeto(self.i2c_addr, bytearray([data]))
