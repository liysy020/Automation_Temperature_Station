from django.db import models
import secrets

def generate_api_key():
    return secrets.token_hex(32) # 64-character hex string

class Device(models.Model):
    DEVICE_CHOICES = [
        ('Temperature Sensor', 'Temperature Sensor'),
        ('Humility Sensor','Humility Sensor'),
        ('Hygrometer Sensor','Hygrometer Sensor')
    ]
    id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50, unique=True)
    Device_Type = models.CharField (choices = DEVICE_CHOICES, default = 'Temperature Sensor')
    Api_Key = models.CharField(max_length=128, blank=True, editable=False)
    Is_Active = models.BooleanField(default=True)
    Created_At = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.Api_Key:
            self.Api_Key = generate_api_key()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.Name

class DeviceData(models.Model):
    id = models.AutoField(primary_key=True)
    Sensor = models.ForeignKey(Device, on_delete=models.CASCADE)
    Temp = models.DecimalField(max_digits=5, decimal_places=1, blank=True)
    Humi = models.DecimalField(max_digits=5, decimal_places=1, blank=True)
    Created_At = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Sensor: {self.Sensor}, Temp: {self.Temp}, Humi: {self.Humi} at {self.Created_At}"