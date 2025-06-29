import onewire, ds18x20
import machine, time

class sensor:
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
