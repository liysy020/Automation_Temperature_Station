import onewire, ds18x20
import machine, time

class sensor_ds18x20:
    def __init__(self, pin):
        # Setup DS18B20
        self.dat = machine.Pin(pin)
        self.ds = ds18x20.DS18X20(onewire.OneWire(self.dat))
        self.roms = self.ds.scan()
    
    def read(self):
        self.ds.convert_temp()
        time.sleep_ms(750)
        for rom in self.roms:
            return round(self.ds.read_temp(rom), 1)

import dht
from machine import Pin
class sensor_dht11:
    def __init__(self, pin):
        self.sensor = dht.DHT11(Pin(pin))

    def read(self, retries=3):
        for _ in range(retries):
            try:
                self.sensor.measure()
                temp = self.sensor.temperature()
                humi = self.sensor.humidity()
                return round(temp, 1), round(humi, 1)
            except OSError:
                pass
        return None
        
class sensor_dht22:
    def __init__(self, pin):
        self.sensor = dht.DHT22(Pin(pin))

    def read(self, retries=3):
        for _ in range(retries):
            try:
                self.sensor.measure()
                temp = self.sensor.temperature()
                humi = self.sensor.humidity()
                return round(temp, 1), round(humi, 1)
            except OSError:
                pass
        return None
        